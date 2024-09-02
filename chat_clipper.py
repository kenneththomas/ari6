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
    
    # Add 1 to include the command message, which we'll remove later
    clipmsg = experimental_container[-(num_messages + 1):]
    # Exclude the last message since it's the command itself
    clipmsg = '\n'.join(clipmsg[:-1])

    return clipmsg

class ConfirmView(View):
    def __init__(self, clipmsg):
        super().__init__()
        self.clipmsg = clipmsg

    @discord.ui.button(label="ye", style=ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        tootlist = aritooter.tootcontrol(self.clipmsg)
        for tootmsg in tootlist:
            await interaction.channel.send(tootmsg)
        await interaction.message.delete()

    @discord.ui.button(label="nah", style=ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.send("Message not posted")
        await interaction.message.delete()

async def handle_chat_clip(message, experimental_container):
    clipmsg = clip_messages(message.content, experimental_container)
    view = ConfirmView(clipmsg)
    await message.channel.send(f"Proposed message to post:\n\n{clipmsg}", view=view)