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

ari_version = '8.5.2'

emoji_storage = {
    'eheu': '<:eheu:233869216002998272>',
    'breez': '<:breez:230153282264236033>',
    'bari': '<:bariblack:638105381549375515>'
}
onlyonce = []
tweetcontainer = []
time_container = []
spanishmode = False

agg_gpt_model = 'gpt-4-0125-preview'
lasttweet = ''
claude = False
dev_mode = False
trivia_answer = ''
trivia_question = ''

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

lastmsg = datetime.datetime.now()
lmcontainer = []
lmcontainer.append(lastmsg)

experimental_container = []

available_languages = ['spanish','french','italian','arabic','chinese','russian','german','korean','greek','japanese','portuguese']


main_enabled = False

starttime = datetime.datetime.now()


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    mememgr.meme_loader()

@client.event
async def on_message(message):
    global claude
    global lastmsg
    global trivia_answer, trivia_question
    #ignore webhooks
    if message.webhook_id:
        return

    global sentience_personality
    if message.author == client.user:
        return
    
    global main_enabled
    global dev_mode
    
    l.log(message)
    experimental_container.append(f'{message.author.display_name}: {message.content}')

    #toggle dev mode, include admin check
    if str(message.content).startswith('!devmode'):
        if ct.admincheck(str(message.author)):
            dev_mode = not dev_mode
            await message.channel.send(f'dev mode is now {dev_mode}')
        else:
            await message.channel.send('u cant do that lol')

    #if in dev_mode dont run any of the following code
    if dev_mode:
        return

    if len(experimental_container) > 10:
        experimental_container.pop(0)

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
            if 'x.com' in message.content:
                tweetlink = message.content.replace('x.com','vxtwitter.com')
                await message.delete() 
                if str(message.channel) == 'gato':
                    catchannel = client.get_channel(205903143471415296)
                    webhooks = await catchannel.webhooks()
                    ari_webhook = next((webhook for webhook in webhooks if webhook.name == 'ari'), None)
                    #pick random webhook from webhook_library
                    personality = random.choice(list(wl.webhook_library.values()))
                    username = personality[0]
                    avatar = personality[1]
                    await ari_webhook.send(f'{message.author.display_name} posted:\n {tweetlink}', username=username, avatar_url=avatar)
                else:
                    await message.channel.send(f"{message.author.display_name} posted:\n {tweetlink}")

    if str(message.content).startswith('!main'):
        if str(message.content).replace('!main','').strip() == 'enable':
            main_enabled = True
            await message.channel.send('main enabled')
        elif str(message.content).replace('!main','').strip() == 'disable':
            main_enabled = False
            await message.channel.send('main disabled')

    #breez aggregation
    global lasttweet


    #toggle claude
    if str(message.content).startswith('!claude'):
        claude = not claude
        await message.channel.send(f'claude is now {claude}')


    if main_enabled == False:
        if message.channel.id == 205903143471415296:
            if str(message.content).startswith('!'):
                print(f'seems like someone is trying to run a command! main disabled tho lol')
            return

    #start AI block

    if True:
        if message.reference:
            if message.reference.resolved.author == client.user:

                #check if that reply had a vxtwitter link in it, if it did, dont reply
                if 'vxtwitter.com' in message.reference.resolved.content:
                    print('DEBUG: not responding to vxtwitter link that was probably posted by me')
                    return

                async with message.channel.typing():
                    if not claude:
                        freemsg = await sentience.ai_experimental(experimental_container,'gpt-4-0125-preview')
                    else:    
                        freemsg = await sentience.claudex(experimental_container)
                    experimental_container.append(f'{freemsg}')
                    await message.reply(freemsg)                    

                return
    
        #basic gpt
        if message.content.startswith('!gpt'):
            response_text = await sentience.generate_text_with_timeout_gpt(message.content)
            await asyncio.sleep(1)
            await message.reply(response_text)

    global spanishmode
    if spanishmode:
        if ct.should_i_spanish(message.content):
                spanish = await sentience.spanish_translation(message.content)
                #people complained about being double pinged by the bot so remove the ping, regex away (<@142508812073566208>)
                spanish = re.sub(r'<@\d+>','',str(spanish))
                catchannel = client.get_channel(1122326983846678638)

                # Create or reuse a single webhook
                webhooks = await catchannel.webhooks()
                spanish_webhook = next((webhook for webhook in webhooks if webhook.name == 'spanish'), None)

                if not spanish_webhook:
                    spanish_webhook = await catchannel.create_webhook(name='spanish')

                await spanish_webhook.send(spanish, username=message.author.name, avatar_url=message.author.avatar)
                #await catchannel.send(f'\n**<{message.author.name}>**\n{spanish}')

    #toggle spanish mode
    if str(message.content).startswith('!spanish'):
        if str(message.content).replace('!spanish','').strip() == 'enable':
            spanishmode = True
            await message.channel.send('spanish mode enabled')
        elif str(message.content).replace('!spanish','').strip() == 'disable':
            spanishmode = False
            await message.channel.send('spanish mode disabled')
        

    #switch sentience.translate_language if !language is called to change translation language
    if str(message.content).startswith('!language'):
        new_language = str(message.content).replace('!language','').strip()
        if new_language in available_languages:
            #use webhook if it exists
            if new_language in wl.language_webhooks.keys():
                # pick random webhook from language_webhooks[new_language] then get username and avatar from webhook_library
                # send message with username and avatar
                translator = random.choice(wl.language_webhooks[new_language])
                translator_name = wl.webhook_library[translator][0]
                translator_avatar = wl.webhook_library[translator][1]
                await spanish_webhook.send(f'#cat language changed to {new_language}', username=translator_name, avatar_url=translator_avatar) 
            else:
                await message.channel.send(f'#cat language changed to {new_language}')
            sentience.translate_language = new_language
        else:
            await message.channel.send(f'{new_language} is not a supported language')

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


    # TODO - this block both replies and reacts so it doesnt fit in emoji reactor or memes
    if message.content.lower().startswith('im '):
        chrasemoji = '<:chras:237738874930069505>'
        chrasreply = message.content.lower()[2:].lstrip()
        if mememgr.chance(12):
            await asyncio.sleep(2)
            await message.add_reaction(chrasemoji)
            if mememgr.chance(6):
                await message.reply(f'hi {chrasreply}')
                await asyncio.sleep(1)
                await message.reply('I\'m ChrasSC')

    if 'https://twitter.com/' in message.content:

        catchannel = client.get_channel(205903143471415296)
        webhooks = await catchannel.webhooks()
        ari_webhook = next((webhook for webhook in webhooks if webhook.name == 'ari'), None)
        if not ari_webhook:
            ari_webhook = await catchannel.create_webhook(name='ari')
    
        #append to tweetcontainer
        #if it is a duplicate, message.reply with "old"
        if message.content in tweetcontainer:
            await message.reply('old')
        else:
            tweetcontainer.append(message.content)

        #embed fixer
        if 'vxtwitter.com' not in message.content:
            if 'twitter.com' in message.content:
                tweetlink = message.content.replace('twitter.com','vxtwitter.com')
                await message.delete()  # delete the original message
                if str(message.channel) == 'gato':
                    #pick random webhook from webhook_library
                    personality = random.choice(list(wl.webhook_library.values()))
                    username = personality[0]
                    avatar = personality[1]
                    await ari_webhook.send(f'{message.author.display_name} posted:\n {tweetlink}', username=username, avatar_url=avatar)
                else:
                    await message.channel.send(f"{message.author.display_name} posted:\n {tweetlink}")

    #ELON
    if 'https://x.com/' in message.content:

        catchannel = client.get_channel(205903143471415296)
        webhooks = await catchannel.webhooks()
        ari_webhook = next((webhook for webhook in webhooks if webhook.name == 'ari'), None)
        if not ari_webhook:
            ari_webhook = await catchannel.create_webhook(name='ari')
    

        #append to tweetcontainer
        #if it is a duplicate, message.reply with "old"
        if message.content in tweetcontainer:
            await message.reply('old')
        else:
            tweetcontainer.append(message.content)
        #embed fixer
            


    #darn tootin
    if message.content.startswith('!toot'):
        toot = message.content.replace('!toot','')
        tootlist = aritooter.tootcontrol(toot)
        for tootmsg in tootlist:
            await message.channel.send(tootmsg)

    # tell me how much xp i have call get_xp_user
    if message.content.startswith('!xp'):
        xp = l.get_xp_user(str(message.author))
        # if xp is not None, send message with xp
        if xp:
            await message.channel.send(f'{message.author} has {xp} xp')


    if message.content == '!trivia':
        #random question
        trivia_question = random.choice(list(l.trivia_questions.keys()))
        trivia_answer = l.trivia_questions[trivia_question]
        async with message.channel.typing():
            host_question = await sentience.ask_trivia_question(trivia_question)
            await message.channel.send(f'{host_question}')

    # if message is answer to trivia question, give xp
    if message.content.lower() == trivia_answer.lower():
        # if trivia answer is blank, dont do anything
        if trivia_answer != '':
            trivia_answer = ''
            l.add_xp_user(str(message.author), 10)
            #await message.channel.send(f'{message.author} got it right! 10 xp')
            async with message.channel.typing():
                congratulatory_msg = await sentience.congratulate_trivia_winner(str(message.author),trivia_question,trivia_answer)
                await message.channel.send(f'{congratulatory_msg}')

    # add trivia question to lumberjack trivia_questions dictionary
    if message.content.startswith('!addquestion'):
        new_trivia = message.content.replace('!addquestion','').strip()
        #split by ,
        #validation, if not 2 items, return
        if len(new_trivia.split(',')) != 2:
            await message.channel.send('Invalid format, use !addquestion question,answer')
            return
        question, answer = [item.strip() for item in new_trivia.split(',')]
        short_uuid = str(uuid.uuid4())[:5]

        l.trivia_questions[question] = answer
        l.newquestion[short_uuid] = [question,answer]
        await message.channel.send(f'Added {question} to trivia questions.\nbreez can save this question with !savequestion {short_uuid}')

    # save trivia question to lumberjack trivia_questions dictionary
    if message.content.startswith('!savequestion'):
        #check if user is admin
        if not ct.admincheck(str(message.author)):
            await message.channel.send('u cant do that lol')
            return
        short_uuid = message.content.replace('!savequestion','').strip()
        if short_uuid in l.newquestion:
            question, answer = l.newquestion[short_uuid]
            l.trivia_questions[question] = answer
            await message.channel.send(f'Saved {question} to trivia questions')
        else:
            await message.channel.send(f'{short_uuid} not found')
    

@client.event
async def on_reaction_add(reaction, user):

    #if reaction emoji is a u emoji, also react with u emoji
    if reaction.emoji == '🇺':
        #TODO: i noticed here if people are spamming the u emoji it will try to do this multiple times and fail/rate limit
        await reaction.message.add_reaction('🇺')

client.run(maricon.bottoken)
