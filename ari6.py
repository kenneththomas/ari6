import discord
import maricon
import lumberjack as l
import mememgr
import asyncio
import control as ct
#import aritooter
import datetime
import sentience
import personality
import multiprocessing

emoji_storage = {
    'eheu': '<:eheu:233869216002998272>',
    'breez': '<:breez:230153282264236033>',
    'bari': '<:bariblack:638105381549375515>'
}
onlyonce = []
tweetcontainer = []
time_container = []
sentience_personality = personality.malik
cm_personality = personality.ari

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

lastmsg = datetime.datetime.now()
lmcontainer = []
lmcontainer.append(lastmsg)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    mememgr.meme_loader()

@client.event
async def on_message(message):
    global lastmsg
    #ignore webhooks
    if message.webhook_id:
        return

    global sentience_personality
    if message.author == client.user:
        return
    
    l.log(message)



    #if someone replies to the bot
    #if str(message.channel) == 'barco' or str(message.channel) == 'config':
    if True:
        if message.reference:
            if message.reference.resolved.author == client.user:
                response_text = await sentience.generate_text_with_timeout_cm(message.content,mememgr.cleanup_username(str(message.author.name)),cm_personality)
                await asyncio.sleep(1)
                await message.reply(response_text)
    
        #basic gpt
        if '!gpt' in str(message.content):
            response_text = await sentience.generate_text_with_timeout_gpt(message.content)
            await asyncio.sleep(1)
            await message.reply(response_text)



    if ct.should_i_spanish(message.content):
        spanish = await sentience.spanish_translation(message.content)
        catchannel = client.get_channel(1122326983846678638)

        #if it has been longer than 1 minute since the last message
        if (datetime.datetime.now() - lmcontainer[0]).total_seconds() > 60:
            lmcontainer[0] = datetime.datetime.now()
            webhook = await catchannel.create_webhook(name=message.author.name)
            await webhook.send(
                str(spanish), username=message.author.name, avatar_url=message.author.avatar)

            webhooks = await catchannel.webhooks()
            for webhook in webhooks:
                await webhook.delete()
        else:
            await catchannel.send(f'\n**<{message.author.name}>**\n{spanish}')

    else:
        print('DEBUG: skipping spanish')


    # sentience control
    '''
    if '!switch' in str(message.content):
        print('switching personality')
        if 'malik' in str(message.content):
            sentience_personality = personality.malik
            await message.reply('personality switched to malik')
        elif 'dasha' in str(message.content):
            sentience_personality = personality.dasha
            await message.reply('personality switched to dasha')
        elif 'bok' in str(message.content):
            sentience_personality = personality.bok
            await message.reply('personality switched to bok')
        elif 'belf' in str(message.content):
            sentience_personality = personality.belf
            await message.reply('YOU WANT BELF! YOU WANT BELF!')

        #clear the conversation history
        sentience.user_conversations = {}
    '''

    # banned words
    bwm = ct.controlmgr(message.content.lower(),str(message.author))
    if bwm.delete == True:
        await message.delete(delay=1)
    if bwm.message:
        await message.channel.send(bwm.message)

    memes = mememgr.memes(message.content.lower())
    for meme in memes:
        await asyncio.sleep(1.5)
        await message.channel.send(meme)


    #call mememgr.emoji_reactor and give the message and author
    #if the emojireactor returns a list with contents react with the contents
    emoji = mememgr.emoji_reactor(message.content.lower(),str(message.author))
    if emoji:
        for emoj in emoji:
            await message.add_reaction(emoj)

    '''
    # TODO - this block both replies and reacts so it doesnt fit in emoji reactor or memes
    #if message content has a link in it, check if it's a twitter link
    if message.content.lower().startswith('im '):
        chrasemoji = '<:chras:237738874930069505>'
        chrasreply = message.content.lower()[2:].lstrip()
        if mememgr.chance(4):
            await asyncio.sleep(2)
            await message.add_reaction(chrasemoji)
            if mememgr.chance(6):
                await message.reply(f'hi {chrasreply}')
                await asyncio.sleep(1)
                await message.reply('I\'m ChrasSC')
    '''

    if 'https://twitter.com/' in message.content:
        #append to tweetcontainer
        #if it is a duplicate, message.reply with "old"
        if message.content in tweetcontainer:
            await message.reply('old')
        else:
            tweetcontainer.append(message.content)
        #if the author of the tweet was @nosetuuz, react fire and heart emojis
        if 'nosetuuz' in message.content:
            await message.add_reaction('🔥')
            await message.add_reaction('❤')

    #stats stuff
    if message.content.startswith('!stats'):
        maxusers = 8
        # if --maxusers is provided in the message, get the number after it
        if '--maxusers' in message.content:
            maxusers = int(message.content.split('--maxusers')[1].lstrip())
            print('maxusers is {}'.format(maxusers))
        statsfile = l.stats(maxusers)
        with open(statsfile, 'rb') as f:
            picture = discord.File(f)
            await message.channel.send('Test:', file=picture)

    '''
    #darn tootin
    if message.content.startswith('!toot'):
        toot = message.content.replace('!toot','')
        tootlist = aritooter.tootcontrol(toot)
        for tootmsg in tootlist:
            await message.channel.send(tootmsg)
    '''


'''
    currenttime = datetime.datetime.now()
    # get most recent item from time_container. if it's older than 5 minutes generate a new response
    try:
        lasttime = time_container[-1]
    except IndexError:
        lasttime = datetime.datetime.now()
    if (currenttime - lasttime).total_seconds() > 120:
        if str(message.channel) == 'gato':
            response_text = await sentience.generate_text_with_timeout_cm(message.content,mememgr.cleanup_username(str(message.author.name)),cm_personality)
            await asyncio.sleep(1)
            await message.reply(response_text)
            bottime = datetime.datetime.now()
            time_container.append(bottime)
'''




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