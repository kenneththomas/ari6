import requests
import base64
import maricon
import os
import time

VISION_MODEL = "google/gemini-2.0-flash-001"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


class ImageReader:
    def __init__(self):
        self.cache = {}

    def _get_openrouter_key(self):
        key = getattr(maricon, "openrouter_key", None) or os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            raise ValueError("OpenRouter key not found (openrouter_key or OPENROUTER_API_KEY)")
        return key

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
        key = self._get_openrouter_key()

        payload = {
            "model": VISION_MODEL,
            "messages": [
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
            ],
            "max_tokens": 1024,
            "temperature": 0.0,
        }

        start_time = time.time()

        try:
            r = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json=payload,
                timeout=60,
            )
            if r.status_code != 200:
                print(f"OpenRouter error {r.status_code}: {r.text}")
                r.raise_for_status()
            data = r.json()

            latency_ms = (time.time() - start_time) * 1000

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            print(f"""
=== IMAGE READER CALL ===
Model: {VISION_MODEL}
Input tokens: {usage.get('prompt_tokens', 'N/A')}
Output tokens: {usage.get('completion_tokens', 'N/A')}
Total tokens: {usage.get('total_tokens', 'N/A')}
Latency: {latency_ms:.0f}ms
Output: {content[:200]}...
=======================
""")

            return content

        except Exception as e:
            print(f"Vision model call failed: {e}")
            return None

    async def get_image_description(self, url: str) -> str | None:
        if url in self.cache:
            print(f"Image cache hit: {url[:50]}...")
            return self.cache[url]

        print(f"Fetching image: {url[:50]}...")
        result = self._fetch_image_base64(url)
        if not result:
            return None

        base64_image, content_type = result
        description = self._call_vision_model(base64_image, content_type)
        if description:
            self.cache[url] = description

        return description


image_reader = ImageReader()