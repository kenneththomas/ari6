import maricon


_bsky_client = None


def _get_bsky_client():
    """Create and authenticate the optional Bluesky client on first use."""
    global _bsky_client
    if _bsky_client is not None:
        return _bsky_client

    username = getattr(maricon, "bskyuser", None)
    password = getattr(maricon, "bskypass", None)
    if not username or not password:
        raise RuntimeError("Bluesky credentials not found")

    try:
        from atproto import Client
    except ImportError as exc:
        raise RuntimeError(
            "Bluesky support is not installed; install requirements_bluesky.txt"
        ) from exc

    client = Client()
    client.login(username, password)
    _bsky_client = client
    return _bsky_client

def tootcontrol(message):
    outputmsg = []
    print('tooting message {}'.format(message))

    try:
        bsky = _get_bsky_client()
        bsky_post = bsky.send_post(text=message)
        outputmsg.append(f"https://bsky.app/profile/{bsky.me.did}/post/{bsky_post.uri.split('/')[-1]}")
    except Exception as e:
        print(f"Bluesky unavailable; post skipped: {e}")

    return outputmsg
