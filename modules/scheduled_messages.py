import asyncio
import csv
import datetime
import hashlib
import json
import os
from zoneinfo import ZoneInfo


SCHEDULED_MESSAGES_STATE_PATH = os.path.join("resources", "scheduled_messages_state.json")

scheduled_messages_jobs = []
scheduled_messages_task = None


async def send_scheduled_message(client, job):
    """Send the scheduled message to the appropriate channel."""
    channel = client.get_channel(job["channel"])
    if channel:
        await channel.send(job["message"])
    else:
        print(f"Channel with ID {job['channel']} not found")


def _scheduled_job_key(job) -> str:
    # Stable, deterministic key for state tracking across restarts.
    base = f"{job.get('channel')}|{job.get('time')}|{job.get('message')}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def _load_scheduled_messages_state() -> dict:
    try:
        with open(SCHEDULED_MESSAGES_STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error reading scheduled messages state: {e}")
        return {}


def _save_scheduled_messages_state(state: dict) -> None:
    try:
        os.makedirs(os.path.dirname(SCHEDULED_MESSAGES_STATE_PATH), exist_ok=True)
        tmp_path = SCHEDULED_MESSAGES_STATE_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp_path, SCHEDULED_MESSAGES_STATE_PATH)
    except Exception as e:
        print(f"Error saving scheduled messages state: {e}")


def load_scheduled_messages():
    """Load scheduled messages from the CSV file."""
    scheduled = []
    state = _load_scheduled_messages_state()
    try:
        with open("resources/scheduled_messages.csv", newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                time_str = row["time"].strip()         # expects format HH:MM (24-hour)
                message = row["message"].strip()
                repeat = row["repeat"].strip().lower() in ["true", "1"]
                channel = int(row["channel"].strip())
                job = {
                    "time": time_str,
                    "message": message,
                    "repeat": repeat,
                    "channel": channel,
                    "last_sent": None  # keeps track of the last day this message was sent
                }
                key = _scheduled_job_key(job)
                last_sent = state.get(key, {}).get("last_sent")
                if isinstance(last_sent, str) and last_sent:
                    try:
                        job["last_sent"] = datetime.date.fromisoformat(last_sent)
                    except ValueError:
                        job["last_sent"] = None

                # If this is a one-time job and it has ever been sent, don't schedule it again.
                if not job["repeat"] and job.get("last_sent") is not None:
                    continue

                scheduled.append(job)
    except Exception as e:
        print(f"Error reading scheduled messages: {e}")
    return scheduled


async def scheduled_messages_loop(client):
    """Loop that checks every 20 seconds to send scheduled messages at the correct EST time."""
    global scheduled_messages_jobs
    while True:
        now = datetime.datetime.now(ZoneInfo("America/New_York"))
        current_time_str = now.strftime("%H:%M")
        current_date = now.date()
        state = None  # lazy-load only if we need to write
        for job in scheduled_messages_jobs[:]:  # iterate on a copy so we can remove non-repeat jobs
            if job["time"] == current_time_str:
                if not job["repeat"]:
                    # non-repeating: send only once, then remove from the list
                    if job.get("last_sent") is None:
                        await send_scheduled_message(client, job)
                        job["last_sent"] = current_date
                        if state is None:
                            state = _load_scheduled_messages_state()
                        state[_scheduled_job_key(job)] = {"last_sent": current_date.isoformat()}
                        _save_scheduled_messages_state(state)
                        scheduled_messages_jobs.remove(job)
                else:
                    # repeating: check if we already sent today
                    if job.get("last_sent") != current_date:
                        await send_scheduled_message(client, job)
                        job["last_sent"] = current_date
                        if state is None:
                            state = _load_scheduled_messages_state()
                        state[_scheduled_job_key(job)] = {"last_sent": current_date.isoformat()}
                        _save_scheduled_messages_state(state)
        await asyncio.sleep(20)


def start_scheduled_messages(client):
    """Reload jobs and start a single scheduler loop for the current Discord client."""
    global scheduled_messages_jobs
    global scheduled_messages_task

    if scheduled_messages_task and not scheduled_messages_task.done():
        try:
            scheduled_messages_task.cancel()
        except Exception:
            pass

    scheduled_messages_jobs = load_scheduled_messages()
    scheduled_messages_task = asyncio.create_task(scheduled_messages_loop(client))
    return scheduled_messages_task
