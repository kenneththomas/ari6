import discord
import asyncio
import random
import sentience
import sentience2
import aritooter as _  # ensures aritooter is loaded (may have side effects)
import re
import modules.image_reader as image_reader
from discord.ui import Button, View


async def _enrich_cxstorage_with_image_descriptions(cxstorage):
    for entry in cxstorage:
        content = entry.get('content', '')
        if '[image_urls]:' in content and '[images]:' not in content:
            urls_match = re.search(r'\[image_urls\]:\s*(.+)', content)
            if not urls_match:
                continue
            urls = [u.strip() for u in urls_match.group(1).split(';') if u.strip()]
            descriptions = []
            for url in urls:
                desc = await image_reader.image_reader.get_image_description(url)
                if desc:
                    descriptions.append(desc)
            if descriptions:
                entry['content'] = content + "\n[images]: " + "; ".join(descriptions)

class ResponseView(View):
    def __init__(self, responses, target_channel, cxstorage):
        super().__init__(timeout=300)  # 5 minute timeout
        self.responses = responses
        self.target_channel = target_channel
        self.cxstorage = cxstorage  # Store cxstorage as instance variable

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

            await _enrich_cxstorage_with_image_descriptions(self.cxstorage)
            responses = []
            for _ in range(2):
                response = await sentience2.generate_text_openrouter(self.cxstorage)
                responses.append(response)

            if self.cxstorage:
                self.cxstorage.pop()
            
            embed = discord.Embed(
                title="Choose which response to send to gato",
                color=0x00ff00
            )
            embed.add_field(name="Option A", value=responses[0], inline=False)
            embed.add_field(name="Option B", value=responses[1], inline=False)
            
            new_view = ResponseView(responses, self.target_channel, self.cxstorage)
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

        await _enrich_cxstorage_with_image_descriptions(cxstorage)

        responses = []
        for _ in range(2):
            response = await sentience2.generate_text_openrouter(cxstorage)
            responses.append(response)

        if cxstorage:
            cxstorage.pop()
        
        embed = discord.Embed(
            title="Choose which response to send to gato",
            color=0x00ff00
        )
        embed.add_field(name="Option A", value=responses[0], inline=False)
        embed.add_field(name="Option B", value=responses[1], inline=False)
        
        view = ResponseView(responses, gatochannel, cxstorage)
        await message.channel.send(embed=embed, view=view)
