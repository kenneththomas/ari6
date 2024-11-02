import discord
import maricon
import lumberjack as l
import mememgr
import asyncio
import control as ct
import aritooter
import datetime
import sentience
import re
import random
import ari_webhooks as wl
import uuid
import ctespn
import cloudhouse
import modules.masta_selecta as masta_selecta
import modules.flipper as flipper
import modules.joey as joey
import chat_clipper
from modules.trivia_handler import TriviaHandler
import modules.response_handler as response_handler
import modules.personal_assistant as pa

ari_version = '8.9.1'

#object to store queued messages that will be sent in the future, contains message, which channel to send it to, when to send it, webhook username and picture
class QueuedMessage:
    def __init__(self, message, channel, when, username, avatar):
        self.message = message
        self.channel = channel
        self.when = when
        self.username = username
        self.avatar = avatar

messagequeue = []
songlibrary = {}

onlyonce = []
tweetcontainer = []
time_container = []
main_enabled = True

lasttweet = ''
dev_mode = False
trivia_answer = ''
trivia_question = ''

intents = discord.Intents.default()

#currently giving all access?
intents.members = True
intents.message_content = True

client = discord.Client(intents=discord.Intents.all())

lastmsg = datetime.datetime.now()
lmcontainer = []
lmcontainer.append(lastmsg)

experimental_container = []
cxstorage = []

available_languages = ['spanish','french','italian','arabic','chinese','russian','german','korean','greek','japanese','portuguese','hebrew']

oldoptions = ['old','😴']

catchannel = None
barcochannel = None
cloudchannel = None
gatochannel = None
botchannel = None


starttime = datetime.datetime.now()

trivia_handler = TriviaHandler()

# Add after other global variables
personal_assistant = pa.PersonalAssistant()

async def get_or_create_webhook(channel, webhook_name):
    """Get existing webhook or create a new one if it doesn't exist"""
    webhooks = await channel.webhooks()
    webhook = next((webhook for webhook in webhooks if webhook.name == webhook_name), None)
    if not webhook:
        webhook = await channel.create_webhook(name=webhook_name)
    return webhook

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    mememgr.meme_loader()

    print('loading channels')
    global catchannel, barcochannel, cloudchannel, gatochannel, botchannel
    catchannel = client.get_channel(1122326983846678638)
    barcochannel = client.get_channel(205930498034237451)
    cloudchannel = client.get_channel(1163165256093286412)
    gatochannel = client.get_channel(205903143471415296)
    botchannel = client.get_channel(613942696763195412)

    # find startup time by subtracting current time from starttime
    rdytime = datetime.datetime.now()
    start_duration = rdytime - starttime
    print(f'Bot started in {start_duration}')



@client.event
async def on_message(message):
    global catchannel, barcochannel, cloudchannel, gatochannel
    global lastmsg, experimental_container
    global trivia_answer, trivia_question
    #ignore webhooks
    if message.webhook_id:
        return

    # Add personal assistant handling
    personal_assistant.add_to_history(message)
    assistant_response = await personal_assistant.handle_message(message)
    if assistant_response:
        await message.reply(assistant_response)
        return

    global sentience_personality
    if message.author == client.user:
        return
    
    global main_enabled
    global dev_mode
    
    l.log(message)
    experimental_container.append(f'{message.author.display_name}: {message.content}')
    cxstorage.append({
            'role': 'user',
            'content': f"{message.author.display_name}: {message.content}"
        })

    #toggle dev mode, include admin check
    if str(message.content).startswith('!devmode'):
        if ct.admincheck(str(message.author)):
            dev_mode = not dev_mode
            await message.channel.send(f'dev mode is now {dev_mode}')
        else:
            cantdothat = await sentience.ucantdothat(message.author, message.content)
            await message.reply(cantdothat)

    #if in dev_mode dont run any of the following code
    if dev_mode:
        return

    if len(experimental_container) > 10:
        experimental_container.pop(0)

    #experimental container can get quite large even with less than 10 messages, if there are more than 500 words across all messages clear the memory
    maxlength = 1000
    total_length = sum(len(s) for s in experimental_container)
    if total_length > maxlength:
        print(f'ALERT: exceeded maxlength {maxlength}, clearing container')
        experimental_container = []

    if len(cxstorage) > 10:
        cxstorage.pop(0)

    if str(message.content).startswith('!version'):
        await message.channel.send(ari_version)

    global starttime
    if str(message.content).startswith('!uptime'):
        currenttime = datetime.datetime.now()
        uptime = currenttime - starttime
        total_seconds = int(uptime.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_string = f"{hours} hours, {minutes} minutes, {seconds} seconds"
        await message.channel.send(uptime_string)

    if str(message.author) == 'breezyexcursion':
        if 'vxtwitter.com' not in message.content:
            if 'https://x.com/' in message.content:
                tweetlink = message.content.replace('x.com','vxtwitter.com')
                await message.delete() 
                if str(message.channel) == 'gato':
                    webhooks = await gatochannel.webhooks()
                    ari_webhook = next((webhook for webhook in webhooks if webhook.name == 'ari'), None)
                    #pick random webhook from webhook_library
                    personality = random.choice(list(wl.webhook_library.values()))
                    username = personality[0]
                    avatar = personality[1]
                    await ari_webhook.send(f'{message.author.display_name} posted:\n {tweetlink}', username=username, avatar_url=avatar)
                else:
                    await message.channel.send(f"{message.author.display_name} posted:\n {tweetlink}")
                return

    #toggle main_enabled with !main
    if str(message.content) == '!main':
        main_enabled = not main_enabled
        await message.channel.send(f'main is now {main_enabled}')

    #other togglers in flipper
    if message.content.startswith('!'):
        togglemsg = flipper.togglemgr(str(message.author), message.content)
        if togglemsg:
            await message.channel.send(togglemsg)

    global lasttweet

    #spotify handling
    if flipper.spotify_enable:
        if message.author.activities:
            for activity in message.author.activities:
                if activity.type == discord.ActivityType.listening:
                    if activity.name == 'Spotify':
                        barco_webhook = await get_or_create_webhook(barcochannel, 'barco')
                        npstring, albumart = masta_selecta.nowplaying(str(message.author), activity)
                        if message.content == '!np':
                            #hacky - if you do !np it could be a dupe, so force it to return with allowrepeat
                            npstring, albumart = masta_selecta.nowplaying(str(message.author), activity, allowrepeat=True)
                        
                        if npstring:
                            l.add_xp_user(str(message.author), 1)
                            # was message !np?
                            if message.content == '!np':
                                await message.channel.send(npstring)
                                if albumart:
                                    await message.channel.send(albumart)
                            else:
                                await barco_webhook.send(npstring, username=message.author.name, avatar_url=message.author.avatar)
                                if albumart:
                                    await barco_webhook.send(albumart, username=message.author.name, avatar_url=message.author.avatar)

                            #roast user's music taste
                            if mememgr.chance(40):
                                roast_prompt = f'{message.author.display_name} is listening to {npstring}, roast them for it. you can comment negative things about the artist or make fun of particular lyrics from that song. end with a skull emoji.'
                                roast = await sentience.generate_text_gpt(roast_prompt,gmodel='gpt-4o')
                                #post as lamelo ball webhook
                                await barco_webhook.send(roast, username='lamelo ball', avatar_url=wl.webhook_library['lamelo ball'][1])


    # anything after this will not work in main if main is disabled
    if main_enabled == False:
        if message.channel.id == 205903143471415296:
            if str(message.content).startswith('!'):
                print(f'seems like someone is trying to run a command! main disabled tho lol')
            return

    if message.content.startswith('!clip'):
        await chat_clipper.handle_chat_clip(message, experimental_container)

    #start AI block

    triggerphrases = ['is this rizz']
    
    if (message.reference and message.reference.resolved.author == client.user) or \
       any(trigger in message.content.lower() for trigger in triggerphrases):
        
        # Check if the referenced message contains a vxtwitter link
        if message.reference and 'vxtwitter.com' in message.reference.resolved.content:
            print('DEBUG: not responding to vxtwitter link that was probably posted by me')
            return

        async with message.channel.typing():
            if not flipper.claude:
                freemsg = await sentience.ai_experimental(experimental_container,'gpt-4o')
                experimental_container.append(f'{freemsg}')
            else:
                print(f'converting to claude format: {cxstorage}')
                cxstorage_formatted = sentience.claudeify(cxstorage)
                freemsg = await sentience.claudex2(cxstorage_formatted)
                cxstorage.append({
                    'role': 'assistant',
                    'content': f"{freemsg}"
                })
            
            # Split and send message
            if freemsg.count('\n') < 6:
                for line in freemsg.split('\n'):
                    if line.strip():
                        await asyncio.sleep(random.uniform(1, 4.3))
                        await message.channel.send(line)
            else:
                await message.reply(freemsg)

        return
    
    #basic gpt
    gmodel = 'gpt-4o-mini'
    if message.content.startswith('!gpt'):
        if message.content.startswith('!gpt4'):
            gmodel = 'gpt-4o'
        if flipper.precheck:
            if 'yes' in await sentience.precheck(message.content):
                await message.reply('popsicle')
                return
        response_text = await sentience.generate_text_gpt(message.content,gmodel=gmodel)
        await asyncio.sleep(1)
        await message.reply(response_text)

    if flipper.translation_enabled:
        if ct.should_i_translate(message.content, message.channel):
            spanish = await sentience.gpt_translation(message.content)
            spanish = re.sub(r'<@\d+>', '', str(spanish))
            
            spanish_webhook = await get_or_create_webhook(catchannel, 'spanish')
            await spanish_webhook.send(spanish, username=message.author.name, avatar_url=message.author.avatar)

        #reverse translation. if there is a post in the spanish channel, translate it back to english

        if message.channel == catchannel:
            if message.content.startswith('xx'):
                message.content = message.content[2:]
                english = await sentience.gpt_translation(message.content, reverse=True)
                english_webhook = await get_or_create_webhook(gatochannel, 'english')
                await english_webhook.send(english, username=message.author.name, avatar_url=message.author.avatar)
            else:
                cathelp = await sentience.generate_text_gpt(f'{message.content}','you are a helpful spanish teacher that is helpful with grammar and vocabulary. if you see words in quotations, translate from english to spanish or vice versa.')
                spanish_webhook = await get_or_create_webhook(catchannel, 'spanish')
                await spanish_webhook.send(cathelp, username='luis', avatar_url='https://res.cloudinary.com/dr2rzyu6p/image/upload/v1710891819/noidfrqtvvxxqkme94vg.jpg')

        
    #switch sentience.translate_language if !language is called to change translation language
    if str(message.content).startswith('!language'):
        new_language = str(message.content).replace('!language','').strip()
        if new_language in available_languages:
            if new_language in wl.language_webhooks.keys():
                spanish_webhook = await get_or_create_webhook(catchannel, 'spanish')
                translator = random.choice(wl.language_webhooks[new_language])
                translator_name = wl.webhook_library[translator][0]
                translator_avatar = wl.webhook_library[translator][1]
                await spanish_webhook.send(f'#cat language changed to {new_language}', 
                                         username=translator_name, 
                                         avatar_url=translator_avatar)
            else:
                await message.channel.send(f'#cat language changed to {new_language}')
            sentience.translate_language = new_language
        else:
            await message.channel.send(f'{new_language} is not a supported language')


    if message.channel == botchannel:
        await response_handler.handle_bot_channel_message(message, cxstorage, gatochannel)
        return

    # end AI block

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

    #ELON
    if 'https://x.com/' in message.content:
        ari_webhook = await get_or_create_webhook(gatochannel, 'ari')
        
        if message.content in tweetcontainer:
            await message.reply(random.choice(oldoptions))
        else:
            tweetcontainer.append(message.content)
            
            if str(message.channel) == 'gato':
                tweetlink = message.content.replace('x.com', 'vxtwitter.com')
                await message.delete()
                personality = random.choice(list(wl.webhook_library.values()))
                username = personality[0]
                avatar = personality[1]
                await ari_webhook.send(f'{message.author.display_name} posted:\n {tweetlink}', username=username, avatar_url=avatar)
            else:
                await message.channel.send(f"{message.author.display_name} posted:\n {tweetlink}")

    #darn tootin
    if message.content.startswith('!toot'):
        #temporary admin check as this toots to my personal account
        if not ct.admincheck(str(message.author)):
            cantdothat = await sentience.ucantdothat(message.author, message.content)
            await message.reply(cantdothat)
        toot = message.content.replace('!toot','')
        tootlist = aritooter.tootcontrol(toot)
        for tootmsg in tootlist:
            await message.channel.send(tootmsg)

    # tell me how much xp i have call get_xp_user
    if message.content.startswith('!xp'):
        #get xp of self if no user is mentioned
        if len(message.content.split(' ')) == 1:
            xp = l.get_xp_user(str(message.author))
            # if xp is not None, send message with xp
            if xp:
                await message.channel.send(f'{message.author} has {xp} xp')
        else:
            #get xp of user mentioned
            user = message.content.split(' ')[1]
            xp = l.get_xp_user(user)
            # if xp is not None, send message with xp
            if xp:
                await message.channel.send(f'{user} has {xp} xp')

    # top 10 xp users
    if message.content == '!top':
        top_users = l.get_top_10_xp_users()
        await message.channel.send(top_users)

    # Trivia commands
    if message.content == '!trivia':
        await trivia_handler.handle_trivia_command(message)
    elif message.content == '!hint':
        await trivia_handler.handle_trivia_hint(message)
    elif message.content.startswith('!addquestion'):
        await trivia_handler.add_trivia_question(message)
    elif message.content.startswith('!savequestion'):
        await trivia_handler.save_trivia_question(message)
    elif message.content == '!triviahelp':
        await trivia_handler.show_help(message)
    else:
        await trivia_handler.check_trivia_answer(message)

    #adjust l.BATCH_SIZE with !batch $number
    if message.content.startswith('!batch'):
        if ct.admincheck(str(message.author)):
            try:
                new_batch_size = int(message.content.replace('!batch','').strip())
                l.BATCH_SIZE = new_batch_size
                await message.channel.send(f'batch size is now {new_batch_size}')
            except:
                await message.channel.send('Invalid batch size')
        else:
            cantdothat = await sentience.ucantdothat(message.author, message.content)
            await message.reply(cantdothat)


    #zoomerposting
    if flipper.zoomerposting:

        # sometimes people post one thought across multiple messages. to give lamelo full context, if the last message was from the same user, append the message to the last message
        if str(message.author) == flipper.zp_last_msg_author:
            flipper.zp_msg = f'{flipper.zp_msg} \n {message.content}'
            print(f'last message was from {flipper.zp_last_msg_author}, appending message to last message, message: {flipper.zp_msg}')
        else:
            flipper.zp_msg = message.content

        flipper.zp_last_msg_author = str(message.author)

        if mememgr.chance(35):
            emoji = await sentience.generate_text_gpt(f'{flipper.zp_msg}','respond to messages with a single emoji that fits the message. the response should be an emoji and nothing else.')
            print(f'message: {flipper.zp_msg} emoji: {emoji}')
            await message.add_reaction(emoji)
        #if channel is barcochannel
        if message.channel == barcochannel:
            if mememgr.chance(8):
                webhooks = await barcochannel.webhooks()
                barco_webhook = next((webhook for webhook in webhooks if webhook.name == 'barco'), None)
                if not barco_webhook:
                    barco_webhook = await barcochannel.create_webhook(name='barco')
                async with barcochannel.typing():
                    zoomerpost = await sentience.generate_text_gpt(f'{flipper.zp_msg}','respond to messages very briefly in the style of a zoomer male in disbelief. if there was a funny-sounding phrase in the message you could say \"he said (message)\", the message should finish with a skull emoji')
                    #post as lamelo ball webhook
                    await barco_webhook.send(zoomerpost, username='lamelo ball', avatar_url=wl.webhook_library['lamelo ball'][1])
        else:
            if mememgr.chance(50):
                async with gatochannel.typing():
                    zoomerpost = await sentience.generate_text_gpt(f'{flipper.zp_msg}','respond to messages very briefly in the style of a zoomer male in disbelief. if there was a funny-sounding phrase in the message you could say \"he said (message)\", the message should finish with a skull emoji','gpt-4o')
                    #send to gatochannel
                    webhooks = await gatochannel.webhooks()
                    ari_webhook = next((webhook for webhook in webhooks if webhook.name == 'ari'), None)
                    await ari_webhook.send(zoomerpost, username='lamelo ball', avatar_url=wl.webhook_library['lamelo ball'][1])
                

    #if message is !ctespn run scoreboard_request and sb_parser
    if message.content == '!ctespn':
        data = ctespn.scoreboard_request()
        ctespn.sb_parser(data)
        for game in ctespn.storage.values():
            await message.channel.send(ctespn.info_printer(game))

    #if message started with && delete it
    if message.content.startswith('&&'):
        print('used forcesubject - deleting message!')
        await message.delete()
    if message.channel == cloudchannel:
        print('cloudhouse channel')
        async with message.channel.typing():
            cloudhouse_message = await cloudhouse.cloudhouse_single(message.author.name, message.content)
        webhook = cloudhouse_message['webhook']
        cmessage = cloudhouse_message['message']

        cloudhouse_webhook = await get_or_create_webhook(cloudchannel, 'cloudhouse')

        try:
            await cloudhouse_webhook.send(cmessage, username=webhook[0], avatar_url=webhook[1])
        except IndexError:
            await cloudchannel.send(cmessage)


    # queued message handler
    for queuedmsg in messagequeue:
        print(f'checking queued message: {queuedmsg.message} {queuedmsg.when} current time: {datetime.datetime.now()}')
        if datetime.datetime.now() > queuedmsg.when:
            print(f'queue time {queuedmsg.when} reached, sending message: {queuedmsg.message}')
            if queuedmsg.channel == cloudchannel:
                cloudhouse_webhook = await get_or_create_webhook(queuedmsg.channel, 'cloudhouse')
                await cloudhouse_webhook.send(queuedmsg.message, username=queuedmsg.username, avatar_url=queuedmsg.avatar)
            else:
                await message.channel.send(queuedmsg.message)

            messagequeue.remove(queuedmsg)


@client.event
async def on_reaction_add(reaction, user):

    #print who reacted and what they reacted with to msg
    print(f'[{datetime.datetime.now()}] {user} reacted with {reaction.emoji} to {reaction.message.author.name}\'s message')
    l.add_xp_user(str(user), 1)

    #if reaction emoji is a u emoji, also react with u emoji
    if reaction.emoji == '🇺':
        #TODO: i noticed here if people are spamming the u emoji it will try to do this multiple times and fail/rate limit
        await reaction.message.add_reaction('🇺')

@client.event
async def on_message_delete(message):
    print(f'[{datetime.datetime.now()}] {message.author.name} deleted message: {message.content}')

client.run(maricon.bottoken)
