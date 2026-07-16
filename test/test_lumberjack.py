import atexit
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

# Keep module import and its additive schema initialization away from real logs.
_IMPORT_DB_DIR = tempfile.TemporaryDirectory()
atexit.register(_IMPORT_DB_DIR.cleanup)
_ORIGINAL_ARI_LOG_DB = os.environ.get("ARI_LOG_DB")
os.environ["ARI_LOG_DB"] = str(Path(_IMPORT_DB_DIR.name) / "import.db")
import lumberjack
if _ORIGINAL_ARI_LOG_DB is None:
    os.environ.pop("ARI_LOG_DB", None)
else:
    os.environ["ARI_LOG_DB"] = _ORIGINAL_ARI_LOG_DB


class LumberjackTelemetryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_dbfilename = lumberjack.dbfilename
        self.original_batch = lumberjack.batch_buffer
        self.original_xp = lumberjack.xp_buffer
        self.original_previous_xp = lumberjack.previous_xp_buffer
        self.original_last_write = lumberjack.last_write_time

        lumberjack.dbfilename = str(Path(self.temp_dir.name) / "telemetry.db")
        lumberjack.batch_buffer = []
        lumberjack.xp_buffer = {}
        lumberjack.previous_xp_buffer = {}
        lumberjack.last_write_time = datetime.now()
        with closing(sqlite3.connect(lumberjack.dbfilename)) as conn:
            lumberjack._ensure_schema(conn)
            conn.commit()

    def tearDown(self):
        lumberjack.dbfilename = self.original_dbfilename
        lumberjack.batch_buffer = self.original_batch
        lumberjack.xp_buffer = self.original_xp
        lumberjack.previous_xp_buffer = self.original_previous_xp
        lumberjack.last_write_time = self.original_last_write
        self.temp_dir.cleanup()

    def test_message_log_includes_stable_discord_identity(self):
        author = SimpleNamespace(
            id=101,
            name="some.user",
            display_name="Some User",
            bot=False,
        )
        channel = SimpleNamespace(id=202, parent_id=303)
        message = SimpleNamespace(
            id=404,
            author=author,
            channel=channel,
            guild=SimpleNamespace(id=505),
            content="hello",
            reference=SimpleNamespace(message_id=606),
            attachments=[object()],
            embeds=[object(), object()],
        )

        lumberjack.log(message)
        lumberjack.flush_to_db()

        with closing(sqlite3.connect(lumberjack.dbfilename)) as conn:
            row = conn.execute(
                """SELECT message_id, author_id, author_display_name,
                          channel_id, guild_id, thread_id,
                          reply_to_message_id, attachment_count, embed_count,
                          timestamp
                   FROM logs"""
            ).fetchone()

        self.assertEqual(row[:9], (
            "404", "101", "Some User", "202", "505", "202", "606", 1, 2
        ))
        self.assertRegex(row[9], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

    def test_reaction_add_and_remove_events_are_stored(self):
        user = SimpleNamespace(
            id=101,
            name="reactor",
            display_name="Reactor",
            bot=False,
        )
        payload = SimpleNamespace(
            emoji=SimpleNamespace(id=707, name="party", __str__=lambda _: "party"),
            message_id=404,
            channel_id=202,
            guild_id=505,
            user_id=101,
            member=user,
        )

        lumberjack.log_reaction_event(payload, "add")
        payload.member = None
        lumberjack.log_reaction_event(payload, "remove")

        with closing(sqlite3.connect(lumberjack.dbfilename)) as conn:
            rows = conn.execute(
                """SELECT action, message_id, reactor_id, emoji_id, emoji_name
                   FROM reaction_events ORDER BY id"""
            ).fetchall()

        self.assertEqual(rows, [
            ("add", "404", "101", "707", "party"),
            ("remove", "404", "101", "707", "party"),
        ])

    def test_ai_call_table_accepts_metadata_only(self):
        lumberjack.log_ai_call(
            provider="openrouter",
            model="provider/model",
            purpose="unit_test",
            input_tokens=10,
            output_tokens=4,
            total_tokens=14,
            latency_ms=123.5,
            attempt_count=2,
            success=True,
            status_code=200,
            cost=0.001,
        )

        with closing(sqlite3.connect(lumberjack.dbfilename)) as conn:
            columns = [row[1] for row in conn.execute("PRAGMA table_info(ai_calls)")]
            row = conn.execute(
                """SELECT provider, model, purpose, input_tokens,
                          output_tokens, total_tokens, attempt_count, success
                   FROM ai_calls"""
            ).fetchone()

        self.assertNotIn("prompt", columns)
        self.assertNotIn("output", columns)
        self.assertEqual(
            row,
            ("openrouter", "provider/model", "unit_test", 10, 4, 14, 2, 1),
        )


if __name__ == "__main__":
    unittest.main()
