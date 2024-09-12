import aritooter
import discord
from discord.ui import Button, View
from discord import ButtonStyle

def clip_messages(content, experimental_container):
    parts = content.split()
    
    # Exclude the command message (assumed to be the last one)
    messages = experimental_container[:-1]
    
    # Remove empty messages
    messages = [msg.strip() for msg in messages if msg.strip()]
    
    # Default to 5 messages
    num_messages = 5
    
    if len(parts) > 1:
        if parts[1].isdigit():
            num_messages = min(int(parts[1]), 10)
        else:
            filterwords = parts[1].split(',')
            messages = [
                msg for msg in messages 
                if any(item.lower() in msg.lower() for item in filterwords)
            ]
    
    # Limit to the specified number
    messages = messages[-num_messages:]
    
    # Create the filtered clipmsg for posting
    filtered_clipmsg = '\n'.join(messages)
    
    # Format the messages for display
    formatted_messages = [
        f"**Message {i}:**\n```\n{msg}\n```" 
        for i, msg in enumerate(messages, 1)
    ]
    
    formatted_clipmsg = '\n\n'.join(formatted_messages)
    return filtered_clipmsg, formatted_clipmsg

class ConfirmView(View):
    def __init__(self, filtered_clipmsg, formatted_clipmsg):
        super().__init__()
        self.filtered_clipmsg = filtered_clipmsg
        self.formatted_clipmsg = formatted_clipmsg

    @discord.ui.button(label="ye", style=ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        tootlist = aritooter.tootcontrol(self.filtered_clipmsg)
        for tootmsg in tootlist:
            await interaction.channel.send(tootmsg)
        await interaction.message.delete()

    @discord.ui.button(label="nah", style=ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.send("Message not posted")
        await interaction.message.delete()

async def handle_chat_clip(message, experimental_container):
    filtered_clipmsg, formatted_clipmsg = clip_messages(message.content, experimental_container)
    view = ConfirmView(filtered_clipmsg, formatted_clipmsg)
    await message.channel.send(f"Proposed message to post:\n\n{formatted_clipmsg}", view=view)