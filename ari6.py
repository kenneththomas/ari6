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
import modules.masta_selecta as masta_selecta
import modules.flipper as flipper
import modules.joey as joey
import chat_clipper
from modules.trivia_handler import TriviaHandler
import modules.response_handler as response_handler
import modules.personal_assistant as pa
from modules.message_queue import MessageQueue
from modules.translator import Translator

ari_version = '8.9.1'

message_queue = MessageQueue()
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

summon_timeout = 120  # Default timeout in seconds

translator = Translator()

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
    # if channel is assistant, add to history
    if str(message.channel) == 'assistant':
        personal_assistant.add_to_history(message)
    assistant_response = await personal_assistant.handle_message(message)
    if assistant_response:
        # we should be using webhooks so typically the response will be handled inside the function
        await message.reply(assistant_response)
        return

    global sentience_personality
    if message.author == client.user:
        return
    
    global main_enabled
    global dev_mode
    
    l.log(message)
    experimental_container.append(f'{message.author.display_name}: {message.content}')
    message_content = f"{message.author.display_name}: {message.content}"
    if not any(msg['content'] == message_content for msg in cxstorage):
        cxstorage.append({
            'role': 'user',
            'content': message_content
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

    # Translation handling
    if flipper.translation_enabled:
        if ct.should_i_translate(message.content, message.channel):
            await translator.handle_translation(message, get_or_create_webhook, catchannel, gatochannel)

    # Language change command
    if str(message.content).startswith('!language'):
        await translator.handle_language_change(message, get_or_create_webhook, catchannel)

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
                tweetlink = message.content.replace('x.com', 'girlcockx.com')
                await message.delete()
                personality = random.choice(list(wl.webhook_library.values()))
                username = personality[0]
                avatar = personality[1]
                await ari_webhook.send(f'{message.author.display_name} posted:\n {tweetlink}', username=username, avatar_url=avatar)
            else:
                await message.channel.send(f"{message.author.display_name} posted:\n {tweetlink}")

    #darn tootin
    if message.content.startswith('!skeet'):
        #temporary admin check as this toots to my personal account
        if not ct.admincheck(str(message.author)):
            cantdothat = await sentience.ucantdothat(message.author, message.content)
            await message.reply(cantdothat)
            return
        toot = message.content.replace('!skeet','').lstrip()
        tootlist = aritooter.tootcontrol(toot)
        for tootmsg in tootlist:
            await message.channel.send(tootmsg)

    # auto skeeter
    if flipper.auto_skeeter > 0 and mememgr.chance(flipper.auto_skeeter):
        print('---auto skeeter---')
        print(cxstorage)
        print('---')
        cxstorage_formatted = sentience.claudeify(cxstorage)
        skeet = await sentience.claudex2(cxstorage_formatted)
        aritooter.tootcontrol(skeet)
        print('posted skeet')

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
        # Aggregate messages from the same author for context
        if str(message.author) == flipper.zp_last_msg_author:
            flipper.zp_msg = f"{flipper.zp_msg}\n{message.content}"
            print(f'Last message was from {flipper.zp_last_msg_author}, appending message: {flipper.zp_msg}')
        else:
            flipper.zp_msg = message.content

        flipper.zp_last_msg_author = str(message.author)

        # Chance to generate and react with an emoji
        if mememgr.chance(35):
            emoji = await sentience.generate_text_gpt(
                flipper.zp_msg,
                "respond to messages with a single emoji that fits the message. the response should be an emoji and nothing else."
            )
            print(f"Message: {flipper.zp_msg} | Emoji: {emoji}")
            await message.add_reaction(emoji)

        # Define common GPT prompt for zoomer response
        zoomer_prompt = (
            'respond to messages very briefly in the style of a zoomer male in disbelief. '
            'if there was a funny-sounding phrase in the message you could say "he said (message)", '
            'the message should finish with a skull emoji'
        )

        # Handle response based on channel
        if message.channel == barcochannel:
            if mememgr.chance(8):
                webhook = await get_or_create_webhook(barcochannel, 'barco')
                async with barcochannel.typing():
                    zoomerpost = await sentience.generate_text_gpt(flipper.zp_msg, zoomer_prompt)
                    await webhook.send(
                        zoomerpost,
                        username='lamelo ball',
                        avatar_url=wl.webhook_library['lamelo ball'][1]
                    )
        else:
            if mememgr.chance(50):
                async with gatochannel.typing():
                    zoomerpost = await sentience.generate_text_gpt(flipper.zp_msg, zoomer_prompt, 'gpt-4o')
                    webhook = await get_or_create_webhook(gatochannel, 'ari')
                    await webhook.send(
                        zoomerpost,
                        username='lamelo ball',
                        avatar_url=wl.webhook_library['lamelo ball'][1]
                    )

    #if message is !ctespn run scoreboard_request and sb_parser
    if message.content == '!ctespn':
        data = ctespn.scoreboard_request()
        ctespn.sb_parser(data)
        for game in ctespn.storage.values():
            await message.channel.send(ctespn.info_printer(game))

    # queued message handler
    await message_queue.process_queue(get_or_create_webhook)

    # Add summon command
    if message.content.startswith('!summon'):
        # Check if user is trying to change timeout
        if ct.admincheck(str(message.author)) and len(message.content.split()) > 1:
            try:
                new_timeout = int(message.content.split()[1])
                global summon_timeout
                summon_timeout = new_timeout
                await message.channel.send(f"Summon timeout set to {new_timeout} seconds")
                return
            except ValueError:
                await message.channel.send("Invalid timeout value")
                return

        # Delete the summon command immediately
        await message.delete()
        # Send a temporary message that can be replied to
        temp_msg = await message.channel.send(f"💭 I'm listening... (this message will delete itself in {summon_timeout}s)")
        # Schedule message deletion
        await asyncio.sleep(summon_timeout)
        try:
            await temp_msg.delete()
        except:
            print("Message already deleted or not found")


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
