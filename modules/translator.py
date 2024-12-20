import re
import random
import sentience
import ari_webhooks as wl

class Translator:
    def __init__(self):
        self.current_language = 'spanish'
        self.available_languages = [
            'spanish', 'french', 'italian', 'arabic', 'chinese',
            'russian', 'german', 'korean', 'greek', 'japanese',
            'portuguese', 'hebrew'
        ]
        self.teacher_avatar = 'https://res.cloudinary.com/dr2rzyu6p/image/upload/v1710891819/noidfrqtvvxxqkme94vg.jpg'

    async def translate(self, text, reverse=False):
        """
        Translate text to/from the current language
        reverse=True means translate back to English
        """
        translated = await sentience.gpt_translation(text, reverse=reverse)
        # Clean up mentions
        return re.sub(r'<@\d+>', '', str(translated))

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
                cathelp = await sentience.generate_text_gpt(
                    f'{message.content}',
                    'you are a helpful spanish teacher that is helpful with grammar and vocabulary. if you see words in quotations, translate from english to spanish or vice versa.'
                )
                spanish_webhook = await get_webhook(catchannel, 'spanish')
                await spanish_webhook.send(cathelp, username='luis', avatar_url=self.teacher_avatar)
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

    def get_current_language(self):
        """Return the currently set language"""
        return self.current_language

    def is_supported_language(self, language):
        """Check if a language is supported"""
        return language.lower() in self.available_languages 