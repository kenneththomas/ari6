import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from modules.persona_commands import handle_persona_command
from modules.persona_output import send_persona_response
from modules.personas import Persona, PersonaStore


class PersonaStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.builtins_path = root / "personas.json"
        self.state_path = root / "personas_state.json"
        self.builtins_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "shared_prompt": "Shared chat rules.",
                    "personas": [
                        {
                            "key": "ari",
                            "display_name": "ari",
                            "avatar_url": "",
                            "prompt": "Default Ari prompt.",
                            "use_bot_identity": True,
                        },
                        {
                            "key": "guest",
                            "display_name": "Guest",
                            "avatar_url": "https://example.com/guest.png",
                            "prompt": "Guest prompt.",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.store = PersonaStore(self.builtins_path, self.state_path)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_public_ari_is_default_without_local_state(self):
        self.assertEqual(self.store.default_key, "ari")
        self.assertTrue(self.store.default().use_bot_identity)
        self.assertIn("Default Ari prompt", self.store.system_prompt())

    def test_custom_persona_and_default_persist(self):
        self.store.save(
            Persona(
                key="new-persona",
                display_name="New Persona",
                avatar_url="https://example.com/new.png",
                prompt="A new prompt.",
            )
        )
        self.store.set_default("new-persona")

        reloaded = PersonaStore(self.builtins_path, self.state_path)

        self.assertEqual(reloaded.default_key, "new-persona")
        self.assertEqual(reloaded.get("new persona").display_name, "New Persona")

    def test_deleting_active_persona_falls_back_to_ari(self):
        self.store.set_default("guest")
        self.store.delete("guest")

        self.assertEqual(self.store.default_key, "ari")
        self.assertIsNone(self.store.get("guest"))

        self.store.reset("guest")
        self.assertEqual(self.store.get("guest").display_name, "Guest")

    def test_ari_cannot_be_deleted(self):
        with self.assertRaisesRegex(ValueError, "cannot be deleted"):
            self.store.delete("ari")


class PersonaCommandTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        builtins_path = root / "personas.json"
        builtins_path.write_text(
            json.dumps(
                {
                    "shared_prompt": "Shared.",
                    "personas": [
                        {
                            "key": "ari",
                            "display_name": "ari",
                            "avatar_url": "",
                            "prompt": "Ari prompt.",
                            "use_bot_identity": True,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        self.store = PersonaStore(builtins_path, root / "state.json")
        self.channel = SimpleNamespace(send=AsyncMock())

    async def asyncTearDown(self):
        self.tempdir.cleanup()

    async def test_admin_can_add_from_discord_attachment_and_select_persona(self):
        message = SimpleNamespace(
            content="!persona add captain | Captain | Talks like a captain.",
            attachments=[SimpleNamespace(url="https://example.com/captain.png")],
            channel=self.channel,
        )

        handled = await handle_persona_command(message, True, self.store)
        await handle_persona_command(
            SimpleNamespace(
                content="!persona use captain",
                attachments=[],
                channel=self.channel,
            ),
            True,
            self.store,
        )

        self.assertTrue(handled)
        self.assertEqual(self.store.default_key, "captain")
        self.assertEqual(
            self.store.get("captain").avatar_url,
            "https://example.com/captain.png",
        )

    async def test_non_admin_cannot_change_default(self):
        message = SimpleNamespace(
            content="!persona use ari",
            attachments=[],
            channel=self.channel,
        )

        await handle_persona_command(message, False, self.store)

        sent_message = self.channel.send.await_args.args[0]
        self.assertIn("do not have permission", sent_message)


class PersonaOutputTests(unittest.IsolatedAsyncioTestCase):
    async def test_custom_persona_uses_webhook_identity(self):
        channel = SimpleNamespace(send=AsyncMock())
        webhook = SimpleNamespace(send=AsyncMock())
        get_webhook = AsyncMock(return_value=webhook)
        persona = Persona(
            key="captain",
            display_name="Captain",
            avatar_url="https://example.com/captain.png",
            prompt="Captain prompt.",
        )

        with patch("modules.persona_output.asyncio.sleep", new=AsyncMock()):
            await send_persona_response(channel, "hello", get_webhook, persona)

        webhook.send.assert_awaited_once_with(
            "hello",
            username="Captain",
            avatar_url="https://example.com/captain.png",
        )
        channel.send.assert_not_awaited()

    async def test_webhook_failure_falls_back_to_bot_identity(self):
        channel = SimpleNamespace(send=AsyncMock())
        get_webhook = AsyncMock(side_effect=RuntimeError("missing permission"))
        persona = Persona(
            key="captain",
            display_name="Captain",
            avatar_url="https://example.com/captain.png",
            prompt="Captain prompt.",
        )

        with patch("modules.persona_output.asyncio.sleep", new=AsyncMock()):
            await send_persona_response(channel, "hello", get_webhook, persona)

        channel.send.assert_awaited_once_with("hello")


if __name__ == "__main__":
    unittest.main()
