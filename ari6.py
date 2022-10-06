import discord
import maricon
import lumberjack as l
import mememgr
import asyncio
import control as ct
import aritooter
#import sentience

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    l.log(message)

    if message.author == client.user:
        return

    # banned words
    bwm = ct.controlmgr(message.content.lower(),str(message.author))
    if bwm.delete == True:
        await message.delete(delay=1)
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

'''
    #sentience
    if message.content == '!talk':
        await message.channel.send(sentience.genmsg())
'''

client.run(maricon.bottoken)