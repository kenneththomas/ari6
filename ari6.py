import discord
import maricon
import lumberjack as l
import mememgr
import asyncio
import control as ct
#import aritooter
import datetime
import sentience
import re
import random
#import sentience2 # local llm instead of openai, for testing
import ari_webhooks as wl

emoji_storage = {
    'eheu': '<:eheu:233869216002998272>',
    'breez': '<:breez:230153282264236033>',
    'bari': '<:bariblack:638105381549375515>'
}
onlyonce = []
tweetcontainer = []
time_container = []
spanishmode = True

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

lastmsg = datetime.datetime.now()
lmcontainer = []
lmcontainer.append(lastmsg)

experimental_container = []

available_languages = ['spanish','french','italian','arabic','chinese','russian','german','korean','greek','japanese','portuguese']




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


    #start AI block

    experimental_container.append(f'{message.author.display_name}: {message.content}')
    if True:
        if message.reference:
            if message.reference.resolved.author == client.user:

                #check if that reply had a vxtwitter link in it, if it did, dont reply
                if 'vxtwitter.com' in message.reference.resolved.content:
                    print('DEBUG: not responding to vxtwitter link that was probably posted by me')
                    return

                async with message.channel.typing():
                    freemsg = await sentience.ai_experimental(experimental_container,'gpt-4-0125-preview')
                    experimental_container.append(f'{freemsg}')
                    await message.reply(freemsg)                    

                return
    
        #basic gpt
        if '!gpt' in str(message.content):
            response_text = await sentience.generate_text_with_timeout_gpt(message.content)
            await asyncio.sleep(1)
            await message.reply(response_text)

    #ari experimental - store last 10 messages in experimental_container
    if len(experimental_container) > 10:
        experimental_container.pop(0)

    '''
    #call ai_experimental from sentience
    if mememgr.chance(3):
        freemsg = await sentience.ai_experimental(experimental_container, 'gpt-4-1106-preview')

        if freemsg:
            experimental_container.append(f'dustin: {freemsg}')
            catchannel = client.get_channel(205930498034237451)
            webhooks = await catchannel.webhooks()
            ari_webhook = next((webhook for webhook in webhooks if webhook.name == 'ari'), None)
            if not ari_webhook:
                ari_webhook = await catchannel.create_webhook(name='ari')
            await ari_webhook.send(freemsg, username='ari', avatar_url='https://res.cloudinary.com/dr2rzyu6p/image/upload/v1702772600/outream/xpa09ll1hpuk3wab0jvr.png')

            #call this again a random number of times from 1-3

            for i in range(random.randint(1,3)):
                personality = random.choice(list(webhook_library.values()))
                username = personality[0]
                avatar = personality[1]
                system_prompt = personality[2]
                freemsg = await sentience.ai_experimental(experimental_container, 'gpt-4-1106-preview', system_prompt)
                experimental_container.append(f'{username}: {freemsg}')
                await ari_webhook.send(freemsg, username=username, avatar_url=avatar)
                await asyncio.sleep(random.randint(1,9))

            return

    '''

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
    #if message content has a link in it, check if it's a twitter link
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
        if 'vxtwitter.com' not in message.content:
            if 'x.com' in message.content:
                tweetlink = message.content.replace('x.com','vxtwitter.com')
                await message.delete()  # delete the original message
                if str(message.channel) == 'gato':
                    #pick random webhook from webhook_library
                    personality = random.choice(list(webhook_library.values()))
                    username = personality[0]
                    avatar = personality[1]
                    await ari_webhook.send(f'{message.author.display_name} posted:\n {tweetlink}', username=username, avatar_url=avatar)
                else:
                    await message.channel.send(f"{message.author.display_name} posted:\n {tweetlink}")


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


client.run(maricon.bottoken)
