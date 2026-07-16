import asyncio
import base64

import requests

import sentience

VISION_MODEL = sentience.GOOGLE_MODEL


class ImageReader:
    def __init__(self):
        self.cache = {}

    def _fetch_image_base64(self, url: str) -> tuple[str, str] | None:
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            content = r.content
            content_type = r.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
            if content_type not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
                content_type = "image/jpeg"
            return base64.b64encode(content).decode("utf-8"), content_type
        except Exception as e:
            print(f"Failed to fetch image from {url}: {e}")
            return None

    def _call_vision_model(self, base64_image: str, content_type: str = "image/jpeg") -> str | None:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in detail. Include any text that appears in the image. Be brief."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{content_type};base64,{base64_image}"
                        }
                    }
                ]
            }
        ]

        try:
            return sentience.openrouter_chat(
                messages=messages,
                model=VISION_MODEL,
                log_style="full",
                max_tokens=1024,
                temperature=0.0,
                timeout=60,
                purpose="image_description",
            )
        except Exception as error:
            print(f"Vision model call failed: {error}")
            return None

    async def get_image_description(self, url: str) -> str | None:
        if url in self.cache:
            print(f"Image cache hit: {url[:50]}...")
            return self.cache[url]

        print(f"Fetching image: {url[:50]}...")
        result = await asyncio.to_thread(self._fetch_image_base64, url)
        if not result:
            return None

        base64_image, content_type = result
        description = await asyncio.to_thread(
            self._call_vision_model,
            base64_image,
            content_type,
        )
        if description:
            self.cache[url] = description

        return description


image_reader = ImageReader()
