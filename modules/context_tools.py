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
