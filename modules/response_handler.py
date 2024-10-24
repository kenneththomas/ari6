import discord
import asyncio
import random
import sentience
from discord.ui import Button, View

class ResponseView(View):
    def __init__(self, responses, target_channel):
        super().__init__(timeout=300)  # 5 minute timeout
        self.responses = responses
        self.target_channel = target_channel

    @discord.ui.button(label="Send A", style=discord.ButtonStyle.green)
    async def send_a_callback(self, interaction: discord.Interaction, button: Button):
        await self._handle_response(interaction, 0)

    @discord.ui.button(label="Send B", style=discord.ButtonStyle.green)
    async def send_b_callback(self, interaction: discord.Interaction, button: Button):
        await self._handle_response(interaction, 1)

    @discord.ui.button(label="Retry", style=discord.ButtonStyle.blurple)
    async def retry_callback(self, interaction: discord.Interaction, button: Button):
        async with interaction.channel.typing():
            if self.cxstorage:
                self.cxstorage.pop()
            
            responses = []
            for _ in range(2):
                cxstorage_formatted = sentience.claudeify(self.cxstorage)
                response = await sentience.claudex2(cxstorage_formatted)
                responses.append(response)
            
            if self.cxstorage:
                self.cxstorage.pop()
            
            embed = discord.Embed(
                title="Choose which response to send to gato",
                color=0x00ff00
            )
            embed.add_field(name="Option A", value=responses[0], inline=False)
            embed.add_field(name="Option B", value=responses[1], inline=False)
            
            new_view = ResponseView(responses, self.target_channel)
            await interaction.message.edit(embed=embed, view=new_view)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()

    async def _handle_response(self, interaction, index):
        if self.responses[index].count('\n') < 6:
            for line in self.responses[index].split('\n'):
                if line.strip():
                    await asyncio.sleep(random.uniform(1, 4.3))
                    await self.target_channel.send(line)
        else:
            await self.target_channel.send(self.responses[index])
        
        self.cxstorage.append({
            'role': 'assistant',
            'content': f"{self.responses[index]}"
        })
        
        await interaction.message.delete()

async def handle_bot_channel_message(message, cxstorage, gatochannel):
    async with message.channel.typing():
        if cxstorage:
            cxstorage.pop()
        
        cxstorage.append({
            'role': 'user',
            'content': f"it's your turn to respond. here's some context for how we expect you to respond: {message.content}"
        })
        
        responses = []
        for _ in range(2):
            cxstorage_formatted = sentience.claudeify(cxstorage)
            response = await sentience.claudex2(cxstorage_formatted)
            responses.append(response)
        
        if cxstorage:
            cxstorage.pop()
        
        embed = discord.Embed(
            title="Choose which response to send to gato",
            color=0x00ff00
        )
        embed.add_field(name="Option A", value=responses[0], inline=False)
        embed.add_field(name="Option B", value=responses[1], inline=False)
        
        view = ResponseView(responses, gatochannel)
        await message.channel.send(embed=embed, view=view)