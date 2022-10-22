import discord
import maricon
import lumberjack as l
import mememgr
import asyncio
import control as ct
import aritooter
import datetime
#import sentience

emoji_storage = {
    'eheu': '<:eheu:233869216002998272>',
    'breez': '<:breez:230153282264236033>',
    'bari': '<:bariblack:638105381549375515>'
}
onlyonce = []
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

    #call mememgr.emoji_reactor and give the message and author
    #if the emojireactor returns a list with contents react with the contents
    emoji = mememgr.emoji_reactor(message.content.lower(),str(message.author))
    if emoji:
        for emoj in emoji:
            await message.add_reaction(emoj)

    # TODO - this block both replies and reacts so it doesnt fit in emoji reactor or memes
    #if message content has a link in it, check if it's a twitter link
    if message.content.lower().startswith('im'):
        chrasemoji = '<:chras:237738874930069505>'
        chrasreply = message.content.lower()[2:].lstrip()
        if mememgr.chance(4):
            asyncio.sleep(2)
            await message.add_reaction(chrasemoji)
            if mememgr.chance(6):
                await message.reply(f'hi {chrasreply}')
                asyncio.sleep(1)
                await message.reply('I\'m ChrasSC')

    if 'https://twitter.com/' in message.content:
        #append to tweetcontainer
        #if it is a duplicate, message.reply with "old"
        if message.content in tweetcontainer:
            await message.reply('old')
        else:
            tweetcontainer.append(message.content)
        #if the author of the tweet was @jaimierz888, react fire and heart emojis
        if 'jaimierz888' in message.content:
            await message.add_reaction('🔥')
            await message.add_reaction('❤')




@client.event
async def on_reaction_add(reaction, user):

    #if reaction emoji is a u emoji, also react with u emoji
    if reaction.emoji == '🇺':
        await reaction.message.add_reaction('🇺')
    
    #if reaction emoji is a bari emoji, also react with bari emoji
    if reaction.emoji == emoji_storage['bari']:
        await reaction.message.add_reaction(emoji_storage['bari'])

    #if reaction emoji is a breez emoji, also react with breez emoji
    if reaction.emoji == emoji_storage['breez']:
        await reaction.message.add_reaction(emoji_storage['breez'])

    #if reaction emoji is a eheu emoji, also react with eheu emoji
    if reaction.emoji == emoji_storage['eheu']:
        await reaction.message.add_reaction(emoji_storage['eheu'])



'''
    #sentience
    if message.content == '!talk':
        await message.channel.send(sentience.genmsg())
'''

client.run(maricon.bottoken)