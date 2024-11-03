import sentience
import personality
import datetime
import asyncio
import random


class PersonalAssistant:
    def __init__(self):
        self.assistant_channel_id = 1302375856265629746
        self.chat_history = []
        self.assistant_history = []
        self.max_history = 10
        self.webhook_name = "assistant"
        self.webhook_avatar = "https://res.cloudinary.com/dr2rzyu6p/image/upload/v1730599540/court-0_2_nxjg1j_ycpknw.jpg"
        self.webhook_username = "courtney"
        self.ast_cxstorage = []
        self.allowed_users = ['breezyexcursion']  # Easy to modify this list later
        self.store_all_users = False  # Flag to toggle storing all users

    def add_to_history(self, message, is_assistant_channel=False, is_bot_response=False):
        """Add message to appropriate history list"""
        if is_bot_response:
            entry = f'Assistant: {message}'
            self.ast_cxstorage.append({
                'role': 'assistant',
                'content': message
            })
        else:
            entry = f'{message.author.display_name}: {message.content}'
            # Only add to cxstorage if it's from allowed users or if store_all_users is True
            if self.store_all_users or str(message.author) in self.allowed_users:
                self.ast_cxstorage.append({
                    'role': 'user',
                    'content': f"{message.author.display_name}: {message.content}"
                })
        
        # Maintain max size of ast_cxstorage
        if len(self.ast_cxstorage) > self.max_history:
            self.ast_cxstorage.pop(0)

        # Regular history management continues as before
        self.chat_history.append(entry)
        if len(self.chat_history) > self.max_history:
            self.chat_history.pop(0)

        if is_assistant_channel:
            self.assistant_history.append(entry)
            if len(self.assistant_history) > self.max_history:
                self.assistant_history.pop(0)

    async def get_or_create_webhook(self, channel):
        """Get existing webhook or create a new one"""
        webhooks = await channel.webhooks()
        webhook = next((webhook for webhook in webhooks if webhook.name == self.webhook_name), None)
        if not webhook:
            webhook = await channel.create_webhook(name=self.webhook_name)
        return webhook

    async def handle_message(self, message):
        """Handle messages in the assistant channel"""
        if message.author.bot:
            return None
        
        if message.channel.id != self.assistant_channel_id:
            return None

        # Use ast_cxstorage for context instead of assistant_history
        system_prompt = (
            f"""You are {self.webhook_username}, Ken (breezyexcursion, but call him ken/kendawg/other nicknames in chat)'s AI assistant.

            first a self summary of yourself:
            {personality.ast_self_summary}

            now about the user:
            {personality.ast_secret_context}

            You are aware that you are currently \"under construction\" and dont have all of your future capabilities.
            You will be particularly excited to help build yourself."

            you respond in lowercase and use zoomer/internet slang but do not use hashtags or emojis.

            current time: {datetime.datetime.now().strftime('%A, %Y-%m-%d %H:%M:%S')}
            """
        )
        
        # Debug print
        print("\n=== ASSISTANT PROMPT ===")
        print(self.ast_cxstorage)
        print("======================\n")
        
        # Convert storage format using claudeify
        formatted_messages = sentience.claudeify(self.ast_cxstorage)
        
        # Get response using formatted messages
        response = await sentience.assistant_claude(messages=formatted_messages, system_prompt=system_prompt, model='claude-3-haiku-20240307')
        
        ##model='claude-3-haiku-20240307' to test and be a bit cheaper
        
        # Add messages to history
        self.add_to_history(message, True)  # Add user message
        self.add_to_history(response, True, True)  # Add bot response
        
        # Get webhook and send response
        webhook = await self.get_or_create_webhook(message.channel)

        # Split and send message based on newlines
        if response.count('\n') < 6:
            for line in response.split('\n'):
                if line.strip():  # Only send non-empty lines
                    await asyncio.sleep(random.uniform(1, 4.3))
                    await webhook.send(
                        content=line,
                        username=self.webhook_username,
                        avatar_url=self.webhook_avatar
                    )
        else:
            await webhook.send(
                content=response,
                username=self.webhook_username,
                avatar_url=self.webhook_avatar
            )
        return None