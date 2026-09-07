import atexit
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord

# Keep lumberjack's import-time schema initialization away from the real log DB.
_IMPORT_DB_DIR = tempfile.TemporaryDirectory()
atexit.register(_IMPORT_DB_DIR.cleanup)
_ORIGINAL_ARI_LOG_DB = os.environ.get('ARI_LOG_DB')
os.environ['ARI_LOG_DB'] = str(Path(_IMPORT_DB_DIR.name) / 'import.db')
from modules import masta_selecta
if _ORIGINAL_ARI_LOG_DB is None:
    os.environ.pop('ARI_LOG_DB', None)
else:
    os.environ['ARI_LOG_DB'] = _ORIGINAL_ARI_LOG_DB


def spotify_activity():
    return SimpleNamespace(
        type=discord.ActivityType.listening,
        name='Spotify',
        artist='Artist One;Artist Two',
        title='A Song',
        album='The Album',
        album_cover_url='https://example.com/cover.jpg',
    )


def message(content, activities):
    author = SimpleNamespace(
        activities=activities,
        name='listener',
        display_name='Listener',
        display_avatar=SimpleNamespace(url='https://example.com/avatar.png'),
    )
    author.__str__ = lambda self: 'listener'
    return SimpleNamespace(
        content=content,
        author=author,
        channel=SimpleNamespace(send=AsyncMock()),
    )


class SpotifyActivityTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        masta_selecta.songlibrary.clear()

    async def test_np_posts_current_spotify_song_without_webhook(self):
        incoming = message('!NP ', [spotify_activity()])
        get_webhook = AsyncMock()

        with (
            patch.object(masta_selecta.l, 'add_xp_user'),
            patch.object(masta_selecta.mememgr, 'chance', return_value=False),
        ):
            handled = await masta_selecta.handle_spotify_activity(
                incoming,
                get_webhook,
                SimpleNamespace(),
            )

        self.assertTrue(handled)
        incoming.channel.send.assert_any_await(
            'Artist One - A Song (ft. Artist Two)\n(The Album)'
        )
        incoming.channel.send.assert_any_await('https://example.com/cover.jpg')
        get_webhook.assert_not_awaited()

    async def test_np_explains_when_spotify_presence_is_unavailable(self):
        incoming = message('!np', [])

        handled = await masta_selecta.handle_spotify_activity(
            incoming,
            AsyncMock(),
            SimpleNamespace(),
        )

        self.assertTrue(handled)
        response = incoming.channel.send.await_args.args[0]
        self.assertIn("can't see a current Spotify song", response)

    async def test_ordinary_message_without_spotify_is_not_handled(self):
        incoming = message('hello', [])

        handled = await masta_selecta.handle_spotify_activity(
            incoming,
            AsyncMock(),
            SimpleNamespace(),
        )

        self.assertFalse(handled)
        incoming.channel.send.assert_not_awaited()

    async def test_automatic_post_uses_current_display_avatar(self):
        incoming = message('hello', [spotify_activity()])
        webhook = SimpleNamespace(send=AsyncMock())
        get_webhook = AsyncMock(return_value=webhook)

        with (
            patch.object(masta_selecta.l, 'add_xp_user'),
            patch.object(masta_selecta.mememgr, 'chance', return_value=False),
        ):
            handled = await masta_selecta.handle_spotify_activity(
                incoming,
                get_webhook,
                SimpleNamespace(),
            )

        self.assertTrue(handled)
        first_send = webhook.send.await_args_list[0]
        self.assertEqual(first_send.kwargs['username'], 'Listener')
        self.assertEqual(
            first_send.kwargs['avatar_url'],
            'https://example.com/avatar.png',
        )


if __name__ == '__main__':
    unittest.main()
