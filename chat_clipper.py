import aritooter
import discord
from discord.ui import Button, View
from discord import ButtonStyle

def clip_messages(content, experimental_container):
    parts = content.split()
    
    # Default to 5 messages, or use the specified number (up to 10)
    num_messages = 5
    if len(parts) > 3 and parts[3].isdigit():
        num_messages = min(int(parts[3]), 10)
    elif len(parts) > 3:
        filterwords = parts[3].split(',')
        experimental_container = [msg for msg in experimental_container if any(item.lower() in msg.lower() for item in filterwords) and msg.strip()]
    
    # Remove empty messages, exclude the last message (command), and limit to the specified number
    messages = [msg.strip() for msg in experimental_container[:-1] if msg.strip()][-num_messages:]
    
    # Create the filtered clipmsg for posting
    filtered_clipmsg = '\n'.join(messages)
    
    # Format the messages for display
    formatted_messages = []
    for i, msg in enumerate(messages, 1):
        formatted_msg = f"**Message {i}:**\n```\n{msg}\n```"
        formatted_messages.append(formatted_msg)
    
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