import datetime
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from modules.scheduled_messages import (
    ScheduledMessagesScheduler,
    UTC,
    handle_scheduled_message_command,
)


class ScheduledMessagesSchedulerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.jobs_path = root / "scheduled_jobs.json"
        self.state_path = root / "scheduled_messages_state.json"
        self.channel = SimpleNamespace(send=AsyncMock())
        self.webhook = SimpleNamespace(send=AsyncMock())
        self.client = SimpleNamespace(get_channel=lambda channel_id: self.channel)
        self.get_webhook = AsyncMock(return_value=self.webhook)

    async def asyncTearDown(self):
        self.tempdir.cleanup()

    def write_jobs(self, jobs):
        self.jobs_path.write_text(
            json.dumps({"schema_version": 1, "jobs": jobs}),
            encoding="utf-8",
        )

    def scheduler(self):
        return ScheduledMessagesScheduler(
            self.client,
            self.get_webhook,
            jobs_path=self.jobs_path,
            state_path=self.state_path,
        )

    async def test_hourly_job_waits_five_minutes_then_uses_webhook_identity(self):
        self.write_jobs(
            [
                {
                    "id": "smoke_alarm",
                    "trigger": {
                        "type": "interval",
                        "seconds": 3600,
                        "initial_delay_seconds": 300,
                    },
                    "action": {
                        "type": "discord_message",
                        "channel": 123,
                        "message": "*chirp*",
                        "webhook": {
                            "name": "smoke alarm",
                            "username": "smoke alarm",
                            "avatar_url": "https://example.com/alarm.png",
                        },
                    },
                }
            ]
        )
        scheduler = self.scheduler()
        start = datetime.datetime(2026, 7, 13, 14, 23, tzinfo=UTC)

        await scheduler.run_once(start)
        self.webhook.send.assert_not_awaited()

        await scheduler.run_once(datetime.datetime(2026, 7, 13, 14, 27, tzinfo=UTC))
        self.webhook.send.assert_not_awaited()

        await scheduler.run_once(datetime.datetime(2026, 7, 13, 14, 28, tzinfo=UTC))
        self.webhook.send.assert_awaited_once_with(
            "*chirp*",
            username="smoke alarm",
            avatar_url="https://example.com/alarm.png",
        )

        await scheduler.run_once(datetime.datetime(2026, 7, 13, 15, 28, tzinfo=UTC))
        self.assertEqual(self.webhook.send.await_count, 2)

    async def test_snooze_delays_job_exactly_24_hours_then_resumes_interval(self):
        self.write_jobs(
            [
                {
                    "id": "smoke_alarm",
                    "trigger": {"type": "interval", "seconds": 3600},
                    "action": {
                        "type": "discord_message",
                        "channel": 123,
                        "message": "*chirp*",
                    },
                }
            ]
        )
        scheduler = self.scheduler()
        changed_at = datetime.datetime(2026, 7, 13, 14, 37, tzinfo=UTC)
        resumes_at = scheduler.snooze_job(
            "smoke_alarm",
            datetime.timedelta(hours=24),
            now=changed_at,
        )

        # A newly constructed scheduler must honor the persisted snooze too.
        scheduler = self.scheduler()

        await scheduler.run_once(resumes_at - datetime.timedelta(seconds=1))
        self.channel.send.assert_not_awaited()

        await scheduler.run_once(resumes_at)
        self.channel.send.assert_awaited_once_with("*chirp*")
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        next_run = datetime.datetime.fromisoformat(
            state["jobs"]["smoke_alarm"]["next_run_at"]
        )
        self.assertEqual(next_run, resumes_at + datetime.timedelta(hours=1))

    async def test_resume_job_ends_snooze_and_runs_immediately(self):
        self.write_jobs(
            [
                {
                    "id": "smoke_alarm",
                    "trigger": {"type": "interval", "seconds": 3600},
                    "action": {
                        "type": "discord_message",
                        "channel": 123,
                        "message": "*chirp*",
                    },
                }
            ]
        )
        scheduler = self.scheduler()
        changed_at = datetime.datetime(2026, 7, 13, 14, 37, tzinfo=UTC)
        removed_at = changed_at + datetime.timedelta(hours=2)
        scheduler.snooze_job(
            "smoke_alarm",
            datetime.timedelta(hours=24),
            now=changed_at,
        )

        self.assertTrue(scheduler.resume_job("smoke_alarm", now=removed_at))
        self.assertFalse(scheduler.resume_job("smoke_alarm", now=removed_at))
        await scheduler.run_once(removed_at)

        self.channel.send.assert_awaited_once_with("*chirp*")

    async def test_daily_job_uses_configured_timezone(self):
        self.write_jobs(
            [
                {
                    "id": "daily_image",
                    "trigger": {
                        "type": "daily",
                        "time": "03:00",
                        "timezone": "America/New_York",
                    },
                    "action": {
                        "type": "discord_message",
                        "channel": 123,
                        "message": "daily",
                    },
                }
            ]
        )
        scheduler = self.scheduler()

        await scheduler.run_once(datetime.datetime(2026, 7, 13, 6, 59, tzinfo=UTC))
        await scheduler.run_once(datetime.datetime(2026, 7, 13, 7, 0, tzinfo=UTC))

        self.channel.send.assert_awaited_once_with("daily")

    async def test_change_battery_command_is_exact_and_available_to_anyone(self):
        message = SimpleNamespace(
            content="!changebattery",
            channel=self.channel,
            author=SimpleNamespace(id=999),
        )

        with patch(
            "modules.scheduled_messages.change_smoke_alarm_battery"
        ) as change_battery:
            handled = await handle_scheduled_message_command(message)

        self.assertTrue(handled)
        change_battery.assert_called_once_with()
        self.channel.send.assert_awaited_once_with(
            "battery changed. the smoke alarm is good for 24 hours"
        )

        ignored = await handle_scheduled_message_command(
            SimpleNamespace(content="!change battery", channel=self.channel)
        )
        self.assertFalse(ignored)

    async def test_remove_battery_command_reenables_chirping_for_anyone(self):
        message = SimpleNamespace(
            content="!removebattery",
            channel=self.channel,
            author=SimpleNamespace(id=999),
        )

        with patch(
            "modules.scheduled_messages.remove_smoke_alarm_battery",
            return_value=True,
        ) as remove_battery:
            handled = await handle_scheduled_message_command(message)

        self.assertTrue(handled)
        remove_battery.assert_called_once_with()
        self.channel.send.assert_awaited_once_with(
            "battery removed. the smoke alarm is chirping again"
        )


if __name__ == "__main__":
    unittest.main()
