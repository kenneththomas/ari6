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
    team1_abbrev: str
    team2_abbrev: str
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
        self.last_plays: Dict[str, str] = {}
        self.teams_to_watch = ["Maryland", "Texas A&M","Michigan","Georgia Tech","Notre Dame","Georgia","Alabama","Iowa"]  # List of teams to watch

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
                team1_abbrev=team1['team']['shortDisplayName'],
                team2_abbrev=team2['team']['shortDisplayName'],
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
        self.storage.clear()
        
        for event in scoreboard_data.get('events', []):
            competition = event['competitions'][0]
            team1, team2 = competition['competitors']
            
            game_info = GameInfo(
                id=event['id'],
                team1=team1['team']['shortDisplayName'],
                team2=team2['team']['shortDisplayName'],
                team1_abbrev=team1['team']['abbreviation'],
                team2_abbrev=team2['team']['abbreviation'],
                last_play=competition.get('situation', {}).get('lastPlay', {}).get('text', 'No last play available'),
                team1_score=team1.get('score', '0'),
                team2_score=team2.get('score', '0'),
                downDistanceText=competition.get('situation', {}).get('downDistanceText', 'No down and distance available'),
                time_qtr=event['status']['type']['detail'],
                team1_logo=team1['team'].get('logo', ''),
                team2_logo=team2['team'].get('logo', '')
            )
            
            if game_info.team1 in self.teams_to_watch or game_info.team2 in self.teams_to_watch:
                self.storage[game_info.id] = game_info
        
        # Debug print
        print(f"Games found after filtering: {len(self.storage)}")
        for game_id, game_info in self.storage.items():
            print(f"Game ID: {game_id}, Teams: {game_info.team1} vs {game_info.team2}")

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
            
            # Post last play as a separate message only if it's different and not "No last play available"
            if (game_info.last_play and 
                game_info.last_play != self.last_plays.get(game_info.id) and 
                game_info.last_play != "No last play available"):
                await channel.send(f"**{game_info.team1_abbrev} vs {game_info.team2_abbrev}**: {game_info.last_play}")
                self.last_plays[game_info.id] = game_info.last_play
        except discord.errors.NotFound:
            # Message not found, send a new one
            embed = self.create_game_embed(game_info)
            new_message = await channel.send(embed=embed)
            game_messages[game_info.id] = (channel.id, new_message.id)

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

@tasks.loop(seconds=15)
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
    print("Fetching and parsing data...")
    cfb_scoreboard.fetch_and_parse_data()
    
    print(f"Teams we're watching: {cfb_scoreboard.teams_to_watch}")
    
    if not cfb_scoreboard.storage:
        await ctx.send("No active games found for the specified teams.")
        print("No games found after filtering.")
        await ctx.message.delete()
        return

    for game_id, game_info in cfb_scoreboard.storage.items():
        print(f"Sending embed for game: {game_info.team1} vs {game_info.team2}")
        embed = cfb_scoreboard.create_game_embed(game_info)
        message = await ctx.send(embed=embed)
        game_messages[game_id] = (ctx.channel.id, message.id)
        await asyncio.sleep(1)  # To avoid hitting rate limits
    
    await ctx.message.delete()

@bot.command(name='cfbhelp')
async def cfb_help(ctx):
    help_embed = discord.Embed(title="CFB Scoreboard Bot Commands", color=0x00ff00)
    help_embed.add_field(name="!cfb", value="Fetch and display current CFB scores", inline=False)
    help_embed.add_field(name="!cfbhelp", value="Display this help message", inline=False)
    await ctx.send(embed=help_embed)

bot.run(maricon.bottoken)