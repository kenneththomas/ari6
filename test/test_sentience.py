import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import sentience
from modules.context_tools import split_discord_message
from modules.image_reader import ImageReader


TRANSPORT_TEST_MODEL = "deepseek/deepseek-v4-flash"


class OpenRouterTransportTests(unittest.TestCase):
    def tearDown(self):
        sentience.set_ai_metadata_logger(None)

    @patch("sentience.requests.post")
    def test_missing_api_key_returns_user_facing_message(self, post):
        with (
            patch.object(sentience, "maricon", SimpleNamespace()),
            patch.dict(os.environ, {}, clear=True),
        ):
            result = sentience.openrouter_chat([], TRANSPORT_TEST_MODEL)

        self.assertEqual(result, sentience.MISSING_API_KEY_MESSAGE)
        post.assert_not_called()

    def test_rejects_non_openrouter_model_identifier(self):
        with self.assertRaisesRegex(ValueError, "provider/model"):
            sentience.openrouter_chat([], "gpt-4o")

    @patch("sentience.requests.post")
    def test_posts_chat_completion_to_openrouter(self, post):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "choices": [{"message": {"content": "hello"}}],
            "usage": {"total_tokens": 3},
        }
        post.return_value = response

        result = sentience.openrouter_chat(
            [{"role": "user", "content": "hi"}],
            TRANSPORT_TEST_MODEL,
            reasoning_disabled=True,
            log_style="lite",
        )

        self.assertEqual(result, "hello")
        response.raise_for_status.assert_called_once_with()
        request = post.call_args
        self.assertEqual(
            request.args[0],
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertEqual(request.kwargs["json"]["model"], TRANSPORT_TEST_MODEL)
        self.assertEqual(request.kwargs["json"]["reasoning"], {"enabled": False})

    @patch("sentience.requests.post")
    def test_emits_metadata_without_prompt_or_output(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": "secret output"}}],
            "usage": {
                "prompt_tokens": 2,
                "completion_tokens": 3,
                "total_tokens": 5,
                "cost": 0.01,
            },
        }
        post.return_value = response
        logger = Mock()
        sentience.set_ai_metadata_logger(logger)

        sentience.openrouter_chat(
            [{"role": "user", "content": "secret input"}],
            TRANSPORT_TEST_MODEL,
            log_style="none",
            purpose="unit_test",
        )

        metadata = logger.call_args.kwargs
        self.assertEqual(metadata["model"], TRANSPORT_TEST_MODEL)
        self.assertEqual(metadata["purpose"], "unit_test")
        self.assertEqual(metadata["total_tokens"], 5)
        self.assertTrue(metadata["success"])
        self.assertNotIn("messages", metadata)
        self.assertNotIn("prompt", metadata)
        self.assertNotIn("output", metadata)

    @patch("sentience.time.sleep")
    @patch("sentience.requests.post")
    def test_retries_rate_limit_response(self, post, sleep):
        rate_limited = Mock(status_code=429, headers={"Retry-After": "0"})
        success = Mock(status_code=200)
        success.json.return_value = {
            "choices": [{"message": {"content": "recovered"}}],
            "usage": {},
        }
        post.side_effect = [rate_limited, success]

        result = sentience.openrouter_chat(
            messages=[{"role": "user", "content": "hi"}],
            model=TRANSPORT_TEST_MODEL,
            log_style="none",
        )

        self.assertEqual(result, "recovered")
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(0.0)

    @patch("sentience.requests.post")
    def test_rejects_malformed_success_response(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {"choices": []}
        post.return_value = response

        with self.assertRaisesRegex(
            sentience.OpenRouterResponseError,
            "without message content",
        ):
            sentience.openrouter_chat(
                messages=[{"role": "user", "content": "hi"}],
                model=TRANSPORT_TEST_MODEL,
                log_style="none",
            )

    @patch("builtins.print")
    @patch("sentience.requests.post")
    def test_content_logging_can_be_toggled(self, post, print_mock):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": "secret output"}}],
            "usage": {},
        }
        post.return_value = response

        sentience.openrouter_chat(
            messages=[{"role": "user", "content": "secret input"}],
            model=TRANSPORT_TEST_MODEL,
            log_style="full",
            log_content=False,
        )

        logged = " ".join(str(call) for call in print_mock.call_args_list)
        self.assertNotIn("secret input", logged)
        self.assertNotIn("secret output", logged)

        print_mock.reset_mock()
        sentience.openrouter_chat(
            messages=[{"role": "user", "content": "secret input"}],
            model=TRANSPORT_TEST_MODEL,
            log_style="full",
            log_content=True,
        )

        logged = " ".join(str(call) for call in print_mock.call_args_list)
        self.assertIn("secret input", logged)
        self.assertIn("secret output", logged)


class ImageReaderTests(unittest.IsolatedAsyncioTestCase):
    @patch("modules.image_reader.sentience.openrouter_chat")
    def test_vision_uses_shared_transport_with_model_default_reasoning(self, chat):
        chat.return_value = "description"

        result = ImageReader()._call_vision_model("encoded-image", "image/png")

        self.assertEqual(result, "description")
        request = chat.call_args.kwargs
        self.assertEqual(request["model"], sentience.GOOGLE_MODEL)
        self.assertNotIn("reasoning_disabled", request)
        image_url = request["messages"][0]["content"][1]["image_url"]["url"]
        self.assertEqual(image_url, "data:image/png;base64,encoded-image")

    @patch("modules.image_reader.asyncio.to_thread", new_callable=AsyncMock)
    async def test_image_network_work_runs_off_event_loop(self, to_thread):
        to_thread.side_effect = [
            ("encoded-image", "image/png"),
            "description",
        ]

        result = await ImageReader().get_image_description("https://example.com/image.png")

        self.assertEqual(result, "description")
        self.assertEqual(to_thread.await_count, 2)


class InformativeModeTests(unittest.IsolatedAsyncioTestCase):
    def test_long_informative_answers_are_split_for_discord(self):
        text = ("first paragraph " * 100) + "\n\n" + ("second paragraph " * 100)

        chunks = split_discord_message(text)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 1900 for chunk in chunks))
        self.assertEqual(" ".join(" ".join(chunks).split()), " ".join(text.split()))

    def test_informative_prompt_keeps_persona_but_overrides_chat_brevity(self):
        prompt = sentience.informative_system_prompt("Ari persona prompt")

        self.assertIn("Ari persona prompt", prompt)
        self.assertIn("Informative mode", prompt)
        self.assertIn("do not apply the persona's usual sentence limit", prompt)
        self.assertIn("clarity and instruction come first", prompt)

    @patch("sentience.asyncio.to_thread", new_callable=AsyncMock)
    async def test_generate_text_accepts_larger_informative_completion_budget(
        self, to_thread
    ):
        to_thread.return_value = "longer instructional answer"

        result = await sentience.generate_text(
            "!gpt explain linked lists",
            sysprompt=sentience.informative_system_prompt("Ari persona prompt"),
            chat_history=[],
            use_context_filter=False,
            max_tokens=sentience.INFORMATIVE_MAX_TOKENS,
        )

        self.assertEqual(result, "longer instructional answer")
        request = to_thread.call_args.kwargs
        self.assertEqual(request["max_tokens"], sentience.INFORMATIVE_MAX_TOKENS)
        self.assertEqual(request["messages"][-1]["content"], "explain linked lists")
        self.assertIn("Informative mode", request["messages"][0]["content"])


if __name__ == "__main__":
    unittest.main()
