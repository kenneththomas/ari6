import datetime

class QueuedMessage:
    def __init__(self, message, channel, when, username, avatar):
        self.message = message
        self.channel = channel
        self.when = when
        self.username = username
        self.avatar = avatar

class MessageQueue:
    def __init__(self):
        self.queue = []

    async def process_queue(self, get_webhook):
        """Process all queued messages that are due"""
        messages_to_remove = []
        for msg in self.queue:
            if datetime.datetime.now() > msg.when:
                if msg.channel.name == 'cloudhouse':  # or however you want to check this
                    webhook = await get_webhook(msg.channel, 'cloudhouse')
                    await webhook.send(msg.message, username=msg.username, avatar_url=msg.avatar)
                else:
                    await msg.channel.send(msg.message)
                messages_to_remove.append(msg)
        
        for msg in messages_to_remove:
            self.queue.remove(msg)

    def add_message(self, message, channel, when, username=None, avatar=None):
        """Add a new message to the queue"""
        queued_msg = QueuedMessage(message, channel, when, username, avatar)
        self.queue.append(queued_msg) 