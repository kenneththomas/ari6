import asyncio
import random
import re

from modules.image_reader import image_reader


DISCORD_MESSAGE_LIMIT = 1900


def split_discord_message(text, limit=DISCORD_MESSAGE_LIMIT):
    """Split text at readable boundaries while staying under Discord's limit."""
    if not text:
        return []

    chunks = []
    remaining = text.strip()
    while len(remaining) > limit:
        split_at = remaining.rfind("\n\n", 0, limit + 1)
        if split_at < limit // 2:
            split_at = remaining.rfind("\n", 0, limit + 1)
        if split_at < limit // 2:
            split_at = remaining.rfind(" ", 0, limit + 1)
        if split_at <= 0:
            split_at = limit

        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()

    if remaining:
        chunks.append(remaining)
    return chunks


async def enrich_cxstorage_with_image_descriptions(cxstorage):
    """Scan chat context for unprocessed image URLs and append image descriptions."""
    for entry in cxstorage:
        content = entry.get('content', '')
        if '[image_urls]:' in content and '[images]:' not in content:
            urls_match = re.search(r'\[image_urls\]:\s*(.+)', content)
            if not urls_match:
                continue

            urls = [url.strip() for url in urls_match.group(1).split(';') if url.strip()]
            descriptions = []
            for url in urls:
                desc = await image_reader.get_image_description(url)
                if desc:
                    descriptions.append(desc)

            if descriptions:
                entry['content'] = content + "\n[images]: " + "; ".join(descriptions)


async def send_ai_response(channel, text, multiline_threshold=8, reply_to=None):
    """Send short AI responses line by line, and long responses as one message."""
    if text.count('\n') < multiline_threshold:
        for line in text.split('\n'):
            for chunk in split_discord_message(line):
                await asyncio.sleep(random.uniform(1, 4.3))
                await channel.send(chunk)
    else:
        chunks = split_discord_message(text)
        for index, chunk in enumerate(chunks):
            if index == 0 and reply_to:
                await reply_to.reply(chunk)
            else:
                await channel.send(chunk)
