import asyncio
import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo


RESOURCE_DIR = Path(__file__).resolve().parent.parent / "resources"
SCHEDULED_JOBS_PATH = RESOURCE_DIR / "scheduled_jobs.json"
SCHEDULED_MESSAGES_STATE_PATH = RESOURCE_DIR / "scheduled_messages_state.json"
UTC = datetime.timezone.utc

scheduled_messages_scheduler = None
scheduled_messages_task = None


def _as_utc(value: datetime.datetime) -> datetime.datetime:
    if value.tzinfo is None:
        raise ValueError("scheduler datetimes must include a timezone")
    return value.astimezone(UTC)


def _parse_datetime(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        return _as_utc(datetime.datetime.fromisoformat(value))
    except ValueError:
        return None


def _serialize_datetime(value: datetime.datetime) -> str:
    return _as_utc(value).isoformat()


class ScheduledMessagesScheduler:
    """Run configured jobs and keep their timing state across bot restarts."""

    def __init__(
        self,
        client,
        get_or_create_webhook,
        jobs_path=SCHEDULED_JOBS_PATH,
        state_path=SCHEDULED_MESSAGES_STATE_PATH,
        now_factory=None,
    ):
        self.client = client
        self.get_or_create_webhook = get_or_create_webhook
        self.jobs_path = Path(jobs_path)
        self.state_path = Path(state_path)
        self.now_factory = now_factory or (lambda: datetime.datetime.now(UTC))
        self.jobs = self._load_jobs()
        self.state = self._load_state()
        self.action_handlers = {
            "discord_message": self._send_discord_message,
        }

    def _load_jobs(self):
        try:
            data = json.loads(self.jobs_path.read_text(encoding="utf-8"))
            jobs = data.get("jobs", [])
            if not isinstance(jobs, list):
                raise ValueError("jobs must be a list")

            seen_ids = set()
            for job in jobs:
                job_id = job.get("id")
                if not isinstance(job_id, str) or not job_id:
                    raise ValueError("every scheduled job must have an id")
                if job_id in seen_ids:
                    raise ValueError(f"duplicate scheduled job id: {job_id}")
                seen_ids.add(job_id)
                self._validate_trigger(job.get("trigger", {}))
                if not isinstance(job.get("action"), dict):
                    raise ValueError(f"scheduled job {job_id} must have an action")
            return jobs
        except FileNotFoundError:
            print(f"Scheduled jobs file not found: {self.jobs_path}")
        except Exception as e:
            print(f"Error reading scheduled jobs: {e}")
        return []

    @staticmethod
    def _validate_trigger(trigger):
        trigger_type = trigger.get("type")
        if trigger_type == "daily":
            datetime.time.fromisoformat(trigger["time"])
            ZoneInfo(trigger["timezone"])
            return
        if trigger_type == "interval":
            if float(trigger["seconds"]) <= 0:
                raise ValueError("interval seconds must be positive")
            if float(trigger.get("initial_delay_seconds", 0)) < 0:
                raise ValueError("interval initial delay must not be negative")
            if trigger.get("align_to") not in (None, "hour"):
                raise ValueError("interval align_to must be 'hour' when provided")
            return
        raise ValueError(f"unsupported trigger type: {trigger_type}")

    def _load_state(self):
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            jobs = data.get("jobs", {})
            return {"jobs": jobs if isinstance(jobs, dict) else {}}
        except FileNotFoundError:
            return {"jobs": {}}
        except Exception as e:
            print(f"Error reading scheduled messages state: {e}")
            return {"jobs": {}}

    def _save_state(self):
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
            tmp_path.write_text(
                json.dumps(self.state, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            tmp_path.replace(self.state_path)
            return True
        except Exception as e:
            print(f"Error saving scheduled messages state: {e}")
            return False

    def register_action(self, name, handler):
        """Register an async action handler for future scheduler integrations."""
        self.action_handlers[name] = handler

    def _job(self, job_id):
        return next((job for job in self.jobs if job["id"] == job_id), None)

    def snooze_job(self, job_id, duration, now=None):
        if self._job(job_id) is None:
            raise KeyError(f"unknown scheduled job: {job_id}")
        now = _as_utc(now or self.now_factory())
        until = now + duration
        job_state = self.state["jobs"].setdefault(job_id, {})
        job_state["snoozed_until"] = _serialize_datetime(until)
        job_state["next_run_at"] = _serialize_datetime(until)
        if not self._save_state():
            raise RuntimeError("could not persist scheduled job state")
        return until

    async def _send_discord_message(self, job):
        action = job["action"]
        channel = self.client.get_channel(int(action["channel"]))
        if channel is None:
            raise RuntimeError(f"Channel with ID {action['channel']} not found")

        webhook_config = action.get("webhook")
        if webhook_config:
            webhook = await self.get_or_create_webhook(
                channel,
                webhook_config["name"],
            )
            await webhook.send(
                action["message"],
                username=webhook_config.get("username", webhook_config["name"]),
                avatar_url=webhook_config.get("avatar_url"),
            )
            return

        await channel.send(action["message"])

    @staticmethod
    def _next_daily_run(trigger, after):
        timezone = ZoneInfo(trigger["timezone"])
        local_after = after.astimezone(timezone)
        scheduled_time = datetime.time.fromisoformat(trigger["time"])
        candidate = datetime.datetime.combine(
            local_after.date(),
            scheduled_time,
            tzinfo=timezone,
        )
        if candidate <= local_after:
            candidate += datetime.timedelta(days=1)
        return candidate.astimezone(UTC)

    @staticmethod
    def _next_interval_run(trigger, after):
        if trigger.get("align_to") == "hour":
            return after.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
        return after + datetime.timedelta(seconds=float(trigger["seconds"]))

    def _initial_run(self, job, now):
        trigger = job["trigger"]
        if trigger["type"] == "daily":
            return self._next_daily_run(trigger, now)
        if "initial_delay_seconds" in trigger:
            return now + datetime.timedelta(
                seconds=float(trigger["initial_delay_seconds"])
            )
        return self._next_interval_run(trigger, now)

    def _run_after_success(self, job, due_at, now):
        trigger = job["trigger"]
        if trigger["type"] == "daily":
            return self._next_daily_run(trigger, now)

        seconds = float(trigger["seconds"])
        next_run = due_at + datetime.timedelta(seconds=seconds)
        while next_run <= now:
            next_run += datetime.timedelta(seconds=seconds)
        return next_run

    async def run_once(self, now=None):
        now = _as_utc(now or self.now_factory())
        state_changed = False

        for job in self.jobs:
            job_id = job["id"]
            job_state = self.state["jobs"].setdefault(job_id, {})
            due_at = _parse_datetime(job_state.get("next_run_at"))
            if due_at is None:
                due_at = self._initial_run(job, now)
                job_state["next_run_at"] = _serialize_datetime(due_at)
                state_changed = True

            snoozed_until = _parse_datetime(job_state.get("snoozed_until"))
            if snoozed_until is not None and snoozed_until > now:
                if due_at != snoozed_until:
                    job_state["next_run_at"] = _serialize_datetime(snoozed_until)
                    state_changed = True
                continue
            if snoozed_until is not None:
                job_state.pop("snoozed_until", None)
                state_changed = True

            if due_at > now:
                continue

            action_name = job["action"].get("type")
            handler = self.action_handlers.get(action_name)
            if handler is None:
                print(f"No action handler registered for scheduled job {job_id}: {action_name}")
                job_state["next_run_at"] = _serialize_datetime(
                    now + datetime.timedelta(minutes=5)
                )
                state_changed = True
                continue

            try:
                await handler(job)
            except Exception as e:
                print(f"Error running scheduled job {job_id}: {e}")
                job_state["next_run_at"] = _serialize_datetime(
                    now + datetime.timedelta(minutes=1)
                )
            else:
                job_state["last_run_at"] = _serialize_datetime(now)
                job_state["next_run_at"] = _serialize_datetime(
                    self._run_after_success(job, due_at, now)
                )
            state_changed = True

        if state_changed:
            self._save_state()

    async def run_forever(self):
        while True:
            await self.run_once()
            await asyncio.sleep(20)


def start_scheduled_messages(client, get_or_create_webhook):
    """Start one scheduler loop for the current Discord client."""
    global scheduled_messages_scheduler
    global scheduled_messages_task

    if scheduled_messages_task and not scheduled_messages_task.done():
        return scheduled_messages_task

    scheduled_messages_scheduler = ScheduledMessagesScheduler(
        client,
        get_or_create_webhook,
    )
    scheduled_messages_task = asyncio.create_task(
        scheduled_messages_scheduler.run_forever()
    )
    return scheduled_messages_task


def change_smoke_alarm_battery(now=None):
    if scheduled_messages_scheduler is None:
        raise RuntimeError("scheduled messages have not started")
    return scheduled_messages_scheduler.snooze_job(
        "smoke_alarm",
        datetime.timedelta(hours=24),
        now=now,
    )


async def handle_scheduled_message_command(message):
    """Handle scheduler commands, returning whether the message was consumed."""
    if message.content.strip().lower() != "!changebattery":
        return False

    try:
        change_smoke_alarm_battery()
        await message.channel.send(
            "battery changed. the smoke alarm is good for 24 hours"
        )
    except (KeyError, RuntimeError) as e:
        print(f"Could not change smoke alarm battery: {e}")
        await message.channel.send("the smoke alarm is not awake yet")
    return True
