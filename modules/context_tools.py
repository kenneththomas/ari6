import asyncio
import random
import re

from modules.image_reader import image_reader


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
            if line.strip():
                await asyncio.sleep(random.uniform(1, 4.3))
                await channel.send(line)
    elif reply_to:
        await reply_to.reply(text)
    else:
        await channel.send(text)
