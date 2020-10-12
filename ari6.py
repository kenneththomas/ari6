import sys
from collections import OrderedDict as odict
import maricon
import discord
import lumberjack as l
import mememgr
import asyncio
import aritooter
import sentience
import control as ct


client = discord.Client()

@client.event
async def on_message(message):

    l.log(message)

    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # banned words
    bwm = ct.controlmgr(message.content.lower(),str(message.author))
    if bwm.delete == True:
        await message.delete(delay=1.5)
    if bwm.message:
        await message.channel.send(bwm.message)

    memes = mememgr.memes(message.content.lower())
    for meme in memes:
        asyncio.sleep(1.5)
        await message.channel.send(meme)

    #darn tootin
    if message.content.startswith('!toot'):
        toot = message.content.replace('!toot','')
        tootlist = aritooter.tootcontrol(toot)
        for tootmsg in tootlist:
            await message.channel.send(tootmsg)

    #sentience
    if message.content == '!talk':
        await message.channel.send(sentience.genmsg())

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    #await client.send_message(discord.Object(id='205903143471415296'), mememgr.startupmsg())


client.run(maricon.bottoken)
