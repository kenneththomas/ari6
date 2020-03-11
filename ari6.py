import sys
from collections import OrderedDict as odict
import maricon
import discord
import lumberjack as l
import asyncio


client = discord.Client()

@client.event
async def on_message(message):

    l.log(message.author,message.content,message.channel)

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    #await client.send_message(discord.Object(id='205903143471415296'), mememgr.startupmsg())


client.run(maricon.bottoken)
