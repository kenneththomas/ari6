import sentience

class PersonalAssistant:
    def __init__(self):
        self.assistant_channel_id = 1302375856265629746
        self.chat_history = []
        self.assistant_history = []
        self.max_history = 10
        self.webhook_name = "assistant"
        self.webhook_avatar = "https://res.cloudinary.com/dr2rzyu6p/image/upload/v1724037683/court-0_2_nxjg1j.jpg"
        self.webhook_username = "courtney"

    def add_to_history(self, message, is_assistant_channel=False, is_bot_response=False):
        """Add message to appropriate history list"""
        if is_bot_response:
            entry = f'Assistant: {message}'
        else:
            entry = f'{message.author.display_name}: {message.content}'
        
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

        # Generate response using more focused context
        context = "\n".join(self.assistant_history)
        
        messages = [{"role": "user", "content": f"Previous conversation:\n{context}\n\nRespond to breezyexcursion: {message.content}"}]
        system_prompt = (
            f"""You are {self.webhook_username}, Ken (bree6 or breez in chat)'s AI assistant.
            You are aware that you are currently \"under construction\" and dont have all of your future capabilities.
            You will be particularly excited to help build yourself."
            """
        )
        
        # Debug print
        print("\n=== ASSISTANT PROMPT ===")
        print(messages)
        print("======================\n")
        
        response = await sentience.assistant_claude(
            messages=messages,
            system_prompt=system_prompt,
            model='claude-3-5-sonnet-20241022'
        )
        self.add_to_history(message, True)  # Add user message to history
        self.add_to_history(response, True, True)  # Add bot response to history
        
        # Get webhook and send response
        webhook = await self.get_or_create_webhook(message.channel)
        await webhook.send(
            content=response,
            username=self.webhook_username,
            avatar_url=self.webhook_avatar
        )
        return None