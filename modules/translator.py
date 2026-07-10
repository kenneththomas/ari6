import re
import random
import asyncio
import sentience
import ari_webhooks as wl

TRANSLATION_MODEL = sentience.GOOGLE_MODEL

class Translator:
    def __init__(self):
        self.current_language = 'spanish'
        self.available_languages = [
            'spanish', 'french', 'italian', 'arabic', 'chinese',
            'russian', 'german', 'korean', 'greek', 'japanese',
            'portuguese', 'hebrew'
        ]

    async def translate(self, text, reverse=False):
        """
        Translate text to/from the current language
        reverse=True means translate back to English
        """
        source_language = self.current_language if reverse else "english"
        target_language = "english" if reverse else self.current_language
        messages = [
            {
                "role": "system",
                "content": (
                    "Translate chatroom messages while keeping similar grammar, "
                    "tone, slang, and formality. Return only the translated text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Translate this message from {source_language} to {target_language}:\n"
                    f"{text}"
                ),
            },
        ]
        try:
            translated = await asyncio.wait_for(
                asyncio.to_thread(
                    sentience.openrouter_chat,
                    messages=messages,
                    model=TRANSLATION_MODEL,
                    reasoning_disabled=True,
                    log_style="lite",
                ),
                timeout=15,
            )
        except asyncio.TimeoutError:
            translated = "obama"

        # Clean up mentions
        return re.sub(r'<@\d+>', '', str(translated))

    async def teach(self, text):
        """Answer questions in language teaching mode."""
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a helpful {self.current_language} teacher that helps "
                    "with grammar and vocabulary. If you see words in quotations, "
                    "translate from english to the target language or vice versa. "
                    "Keep the response concise and informal."
                ),
            },
            {"role": "user", "content": text},
        ]
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(
                    sentience.openrouter_chat,
                    messages=messages,
                    model=TRANSLATION_MODEL,
                    reasoning_disabled=True,
                    log_style="lite",
                ),
                timeout=15,
            )
        except asyncio.TimeoutError:
            return "obama"

    async def handle_translation(self, message, get_webhook, catchannel, gatochannel):
        """Handle translation of a message including webhook management"""
        if message.channel == catchannel:
            if message.content.startswith('xx'):
                # Reverse translation (to English)
                english = await self.translate(message.content[2:], reverse=True)
                english_webhook = await get_webhook(gatochannel, 'english')
                await english_webhook.send(english, username=message.author.name, avatar_url=message.author.avatar)
            else:
                # Language teaching mode
                cathelp = await self.teach(message.content)
                spanish_webhook = await get_webhook(catchannel, 'spanish')
                await spanish_webhook.send(
                    cathelp,
                    username=wl.webhook_library['luis'][0],
                    avatar_url=wl.webhook_library['luis'][1],
                )
        else:
            # Normal translation
            translated = await self.translate(message.content)
            spanish_webhook = await get_webhook(catchannel, 'spanish')
            await spanish_webhook.send(translated, username=message.author.name, avatar_url=message.author.avatar)

    async def handle_language_change(self, message, get_webhook, catchannel):
        """Handle language change command and response"""
        new_language = message.content.replace('!language', '').strip()
        success, response = self.change_language(new_language)
        
        if success:
            if new_language in wl.language_webhooks:
                webhook = await get_webhook(catchannel, 'spanish')
                translator_choice = random.choice(wl.language_webhooks[new_language])
                translator_name = wl.webhook_library[translator_choice][0]
                translator_avatar = wl.webhook_library[translator_choice][1]
                await webhook.send(
                    f'#cat {response}',
                    username=translator_name,
                    avatar_url=translator_avatar
                )
            else:
                await message.channel.send(f'#cat {response}')
        else:
            await message.channel.send(response)

    def change_language(self, new_language):
        """
        Attempt to change the translation language
        Returns (success, message)
        """
        if new_language.lower() in self.available_languages:
            self.current_language = new_language.lower()
            return True, f"Translation language changed to {new_language}"
        return False, f"{new_language} is not a supported language"
