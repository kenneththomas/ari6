import sentience
import personality
import datetime
import asyncio
import random


class PersonalAssistant:
    def __init__(self):
        # Channel configurations
        self.assistant_channels = {
            'breezyexcursion': {
                'channel_id': 1302375856265629746,
                'webhook_name': "assistant",
                'webhook_avatar': "https://res.cloudinary.com/dr2rzyu6p/image/upload/v1730599540/court-0_2_nxjg1j_ycpknw.jpg",
                'webhook_username': "courtney",
                'history': [],
                'cxstorage': [],
                'system_prompt': """You are courtney, breezyexcursion's AI assistant.

                first a self summary of yourself:
                {personality.ast_self_summary}

                now about the user:
                {personality.ast_secret_context}

                You are aware that you are currently \"under construction\" and dont have all of your future capabilities.
                You will be particularly excited to help build yourself."

                you respond in lowercase and use zoomer/internet slang but do not use hashtags or emojis. messages are kept short unless explaining something specific"""
            },
            'bookmire': {
                'channel_id': 1303780689681977416,
                'webhook_name': "assistant",
                'webhook_avatar': "https://res.cloudinary.com/dr2rzyu6p/image/upload/v1710891776/samples/chair.png",
                'webhook_username': "chair",
                'history': [],
                'cxstorage': [],
                'system_prompt': """You are chair, bookmire's AI assistant.

                first a self summary of yourself:
                You are a helpful, friendly AI assistant who likes to keep things simple and straightforward.
                You enjoy helping bookmire with various tasks and questions.

                now about the user:
                bookmire is a thoughtful and curious person who appreciates clear and concise information.
                """
            }
        }
        
        # Legacy variables for backward compatibility
        self.assistant_channel_id = 1302375856265629746  # breezyexcursion's channel
        self.chat_history = []
        self.assistant_history = []
        self.max_history = 10
        self.webhook_name = "assistant"
        self.webhook_avatar = "https://res.cloudinary.com/dr2rzyu6p/image/upload/v1730599540/court-0_2_nxjg1j_ycpknw.jpg"
        self.webhook_username = "courtney"
        self.ast_cxstorage = []
        self.allowed_users = ['breezyexcursion', 'bookmire']  # Added bookmire
        self.store_all_users = False  # Flag to toggle storing all users

    def add_to_history(self, message, is_assistant_channel=False, is_bot_response=False):
        """Add message to appropriate history list"""
        # Determine which user's channel this is
        user_id = None
        
        if is_bot_response and isinstance(message, str):
            # Handle string responses differently
            entry = f'Assistant: {message}'
            
            # Add to legacy storage
            self.ast_cxstorage.append({
                'role': 'assistant',
                'content': message
            })
            
            # Add to all user-specific storages that have recent activity
            for user, config in self.assistant_channels.items():
                if config['cxstorage']:  # Only add to channels with existing conversation
                    config['cxstorage'].append({
                        'role': 'assistant',
                        'content': message
                    })
                    # Maintain max size
                    if len(config['cxstorage']) > self.max_history:
                        config['cxstorage'].pop(0)
                    
                    # Add to user-specific history
                    config['history'].append(entry)
                    if len(config['history']) > self.max_history:
                        config['history'].pop(0)
            
            # Legacy history management
            self.chat_history.append(entry)
            if len(self.chat_history) > self.max_history:
                self.chat_history.pop(0)
            
            self.assistant_history.append(entry)
            if len(self.assistant_history) > self.max_history:
                self.assistant_history.pop(0)
            
            return
        
        # Original message object handling
        for user, config in self.assistant_channels.items():
            if hasattr(message, 'channel') and message.channel.id == config['channel_id']:
                user_id = user
                break
        
        if not is_bot_response:
            entry = f'{message.author.display_name}: {message.content}'
            
            # Add to user-specific storage if applicable
            if user_id and (self.store_all_users or str(message.author) in self.allowed_users):
                self.assistant_channels[user_id]['cxstorage'].append({
                    'role': 'user',
                    'content': f"{message.author.display_name}: {message.content}"
                })
                # Maintain max size
                if len(self.assistant_channels[user_id]['cxstorage']) > self.max_history:
                    self.assistant_channels[user_id]['cxstorage'].pop(0)
            
            # Legacy storage
            if self.store_all_users or str(message.author) in self.allowed_users:
                self.ast_cxstorage.append({
                    'role': 'user',
                    'content': f"{message.author.display_name}: {message.content}"
                })
        
        # Maintain max size of legacy storage
        if len(self.ast_cxstorage) > self.max_history:
            self.ast_cxstorage.pop(0)

        # Add to user-specific history if applicable
        if user_id:
            self.assistant_channels[user_id]['history'].append(entry)
            if len(self.assistant_channels[user_id]['history']) > self.max_history:
                self.assistant_channels[user_id]['history'].pop(0)

        # Legacy history management
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
        
        # Check if message is in any of the configured assistant channels
        user_id = None
        for user, config in self.assistant_channels.items():
            if message.channel.id == config['channel_id']:
                user_id = user
                break
                
        if not user_id:
            return None

        # Add user message to history first
        self.add_to_history(message, True)

        # Use channel-specific configuration
        channel_config = self.assistant_channels[user_id]
        
        # Use user-specific system prompt with current time added
        system_prompt = channel_config['system_prompt'] + f"\n\ncurrent time: {datetime.datetime.now().strftime('%A, %Y-%m-%d %H:%M:%S')}"
        
        # Debug print
        print(f"\n=== ASSISTANT PROMPT FOR {user_id} ===")
        print(channel_config['cxstorage'])
        print("======================\n")
        
        # Convert storage format using claudeify
        formatted_messages = sentience.claudeify(channel_config['cxstorage'])
        
        # Get response using formatted messages
        response = await sentience.assistant_claude(messages=formatted_messages, system_prompt=system_prompt, model='claude-3-haiku-20240307')
        
        # Add bot response to history
        self.add_to_history(response, True, True)
        
        # Get webhook and send response
        webhook = await self.get_or_create_webhook(message.channel)

        # Split and send message based on newlines
        if response.count('\n') < 6:
            for line in response.split('\n'):
                if line.strip():  # Only send non-empty lines
                    await asyncio.sleep(random.uniform(1, 4.3))
                    await webhook.send(
                        content=line,
                        username=channel_config['webhook_username'],
                        avatar_url=channel_config['webhook_avatar']
                    )
        else:
            await webhook.send(
                content=response,
                username=channel_config['webhook_username'],
                avatar_url=channel_config['webhook_avatar']
            )
        return None