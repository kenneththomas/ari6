import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import aritooter


class BlueskyTests(unittest.TestCase):
    def setUp(self):
        aritooter._bsky_client = None

    def tearDown(self):
        aritooter._bsky_client = None

    def test_client_is_not_created_during_import(self):
        self.assertIsNone(aritooter._bsky_client)

    @patch("builtins.print")
    @patch("aritooter._get_bsky_client")
    def test_unavailable_bluesky_skips_post(self, get_client, print_mock):
        get_client.side_effect = RuntimeError("Bluesky credentials not found")

        result = aritooter.tootcontrol("hello")

        self.assertEqual(result, [])
        self.assertIn("post skipped", str(print_mock.call_args_list))

    @patch("aritooter._get_bsky_client")
    def test_successful_post_returns_bluesky_url(self, get_client):
        client = Mock()
        client.me.did = "did:plc:test"
        client.send_post.return_value = SimpleNamespace(uri="at://did:plc:test/app.bsky.feed.post/abc")
        get_client.return_value = client

        result = aritooter.tootcontrol("hello")

        self.assertEqual(result, ["https://bsky.app/profile/did:plc:test/post/abc"])
        client.send_post.assert_called_once_with(text="hello")


if __name__ == "__main__":
    unittest.main()
