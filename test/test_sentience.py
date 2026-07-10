import unittest
from unittest.mock import Mock, patch

import sentience


TRANSPORT_TEST_MODEL = "deepseek/deepseek-v4-flash"


class OpenRouterTransportTests(unittest.TestCase):
    def test_rejects_non_openrouter_model_identifier(self):
        with self.assertRaisesRegex(ValueError, "provider/model"):
            sentience._openrouter_chat([], "gpt-4o")

    @patch("sentience.requests.post")
    def test_posts_chat_completion_to_openrouter(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": "hello"}}],
            "usage": {"total_tokens": 3},
        }
        post.return_value = response

        result = sentience._openrouter_chat(
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


if __name__ == "__main__":
    unittest.main()
