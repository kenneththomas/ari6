import discord
from discord.ext import commands, tasks
import asyncio
import requests
from dataclasses import dataclass
from typing import Dict
import datetime
import maricon

@dataclass
class GameInfo:
    id: str
    team1: str
    team2: str
    last_play: str
    team1_score: str
    team2_score: str
    downDistanceText: str
    time_qtr: str
    team1_logo: str
    team2_logo: str

class CFBScoreboard:
    API_URL = 'https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard'

    def __init__(self):
        self.storage: Dict[str, GameInfo] = {}

    def fetch_scoreboard_data(self) -> dict:
        response = requests.get(self.API_URL)
        response.raise_for_status()
        return response.json()

    def parse_scoreboard_data(self, scoreboard_data: dict) -> None:
        self.storage.clear()
        for event in scoreboard_data['events']:
            if event['status']['type']['completed']:
                continue

            competition = event['competitions'][0]
            team1, team2 = competition['competitors']

            game_info = GameInfo(
                id=event['id'],
                team1=team1['team']['displayName'],
                team2=team2['team']['displayName'],
                last_play=competition.get('situation', {}).get('lastPlay', {}).get('text', 'No last play available'),
                team1_score=team1['score'],
                team2_score=team2['score'],
                downDistanceText=competition.get('situation', {}).get('downDistanceText', 'No down and distance available'),
                time_qtr=event['status']['type']['detail'],
                team1_logo=team1['team']['logo'],
                team2_logo=team2['team']['logo']
            )

            self.storage[game_info.id] = game_info

    def fetch_and_parse_data(self) -> None:
        scoreboard_data = self.fetch_scoreboard_data()
        self.parse_scoreboard_data(scoreboard_data)

    def create_game_embed(self, game_info: GameInfo) -> discord.Embed:
        embed = discord.Embed(title="scoreboard", color=0x0099ff)
        embed.add_field(name=game_info.team1, value=game_info.team1_score, inline=True)
        embed.add_field(name=game_info.team2, value=game_info.team2_score, inline=True)
        embed.add_field(name="Game Status", value=f"{game_info.downDistanceText}\n{game_info.time_qtr}", inline=False)
        embed.add_field(name="Last Play", value=game_info.last_play, inline=False)
        embed.set_thumbnail(url=game_info.team1_logo)
        embed.set_footer(text=f"Game ID: {game_info.id} | Updated at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return embed

    async def update_game_message(self, channel, message_id, game_info):
        try:
            message = await channel.fetch_message(message_id)
            embed = self.create_game_embed(game_info)
            await message.edit(embed=embed)
        except discord.errors.NotFound:
            # Message not found, send a new one
            embed = self.create_game_embed(game_info)
            await channel.send(embed=embed)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
cfb_scoreboard = CFBScoreboard()

# Dictionary to store the last message ID for each game
game_messages = {}

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    update_scores.start()

@tasks.loop(seconds=90)
async def update_scores():
    cfb_scoreboard.fetch_and_parse_data()
    
    for game_id, game_info in cfb_scoreboard.storage.items():
        if game_id in game_messages:
            channel_id, message_id = game_messages[game_id]
            channel = bot.get_channel(channel_id)
            if channel:
                await cfb_scoreboard.update_game_message(channel, message_id, game_info)

@bot.command(name='cfb')
async def cfb_scores(ctx):
    cfb_scoreboard.fetch_and_parse_data()
    
    if not cfb_scoreboard.storage:
        await ctx.send("No active games found.")
        return

    for game_id, game_info in cfb_scoreboard.storage.items():
        embed = cfb_scoreboard.create_game_embed(game_info)
        message = await ctx.send(embed=embed)
        game_messages[game_id] = (ctx.channel.id, message.id)
        await asyncio.sleep(1)  # To avoid hitting rate limits

@bot.command(name='cfbhelp')
async def cfb_help(ctx):
    help_embed = discord.Embed(title="CFB Scoreboard Bot Commands", color=0x00ff00)
    help_embed.add_field(name="!cfb", value="Fetch and display current CFB scores", inline=False)
    help_embed.add_field(name="!cfbhelp", value="Display this help message", inline=False)
    await ctx.send(embed=help_embed)

bot.run(maricon.bottoken)