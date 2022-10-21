import discord
import maricon
import lumberjack as l
import mememgr
import asyncio
import control as ct
import aritooter
#import sentience

tweetcontainer = []
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    mememgr.meme_loader()

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


    #TODO - move this into meme module or something
    #TODO - add test when moved into meme module
    if message.content.lower().startswith('im'):
        chrasemoji = '<:chras:237738874930069505>'
        chrasreply = message.content.lower()[2:].lstrip()
        if mememgr.chance(2):
            asyncio.sleep(2)
            await message.add_reaction(chrasemoji)
            if mememgr.chance(2):
                await message.reply(f'hi {chrasreply}')
                asyncio.sleep(1)
                await message.reply('I\'m ChrasSC')


    #if message content has a link in it, check if it's a twitter link
    if 'https://twitter.com/' in message.content:
        #append to tweetcontainer
        #if it is a duplicate, message.reply with "old"
        if message.content in tweetcontainer:
            await message.reply('old')
        else:
            tweetcontainer.append(message.content)
        print(tweetcontainer)

    #call mememgr.emoji_reactor and give the message and author
    #if the emojireactor returns a list with contents react with the contents
    emoji = mememgr.emoji_reactor(message.content.lower(),str(message.author))
    if emoji:
        for emoj in emoji:
            await message.add_reaction(emoj)


'''
    #sentience
    if message.content == '!talk':
        await message.channel.send(sentience.genmsg())
'''

client.run(maricon.bottoken)