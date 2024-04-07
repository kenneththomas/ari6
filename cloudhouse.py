import ari_webhooks
import random
import sentience
import personality
import re
import datetime
import modules.flipper as flipper

#object that we return, has webhook and message

members = personality.members
mainchars = personality.mainchars
chathistory = []

claudemodels = ['claude-3-sonnet-20240229','claude-3-haiku-20240307','claude-3-opus-20240229']

async def cloudhouse(user, message, replyto=None):
    bestmodel = False
    forcesubject = None

    
    # select random member of cloudhouse
    #can call a specific friend with --friendname
    if message.startswith('--'):
        friend = message.split()[0][2:]
        #strip the friendname from the message
        message = ' '.join(message.split()[1:])
        print(f'calling a specific friend: {friend}')
        bestmodel = True
    else:
        friend = random.choice(members)
    if message.startswith('&&'):
        #specific user
        friend = message.split()[0][2:]
        #strip the friendname from the message
        message = ' '.join(message.split()[1:])
        print(f'calling a specific friend: {friend}')
        bestmodel = True
        forcesubject = message
        message = ''
    else:
        #add to chathistory
        chathistory.append(f'{user}: {message}')
        print(f'debug chathistory: {chathistory}')
    # get webhook from either ari_webhooks or personality.pwhl
    all_webhooks = {**ari_webhooks.webhook_library, **personality.pwhl}
    try:
        webhook = all_webhooks[friend]
    except KeyError:
        # somebody tried to call a friend that doesn't exist :(
        friend = random.choice(members)
        webhook = all_webhooks[friend]
    username = webhook[0]
    #debug
    try:
        description = webhook[2]
    except IndexError:
        print(f'error getting description for {username}')
        description = ''
    prompt = f'{personality.cloudhouse_prompt} information about your character and personality, {username} : {description}'
    if forcesubject:
        prompt = f'{prompt} subject of the message: {forcesubject}'
    print(prompt)
    # get message
    if friend in mainchars:
        if not bestmodel:
            cmodel = random.choice(claudemodels)
            print(f'using random claudemodel: {cmodel}')
        else:
            print('using the best model as specific friend was requested')
            cmodel = 'claude-3-opus-20240229'
        print('chosen claudemodel:', cmodel)
        chresponse = await sentience.ch_claudex(prompt,chathistory,cmodel)
    else:
        #turn chathistory into a string
        chstring = ' '.join(chathistory)
        chresponse = await sentience.generate_text_gpt(chstring,prompt,'gpt-4-0125-preview')

    #sometimes this responds with the username, if there is a : in the first word, regex to remove the first word
    if re.match(r'^\w+:',chresponse):
        chresponse = chresponse.split(':',1)[1]

    chathistory.append(f'{username}: {chresponse}')

    return {'webhook':webhook,'message':chresponse}

async def cloudhouse_single(user, message, replyto=None):
    forcesubject = False
    skip_history = False
    friend = personality.singlechar

    if str(user) == 'breezyexcursion':
        print(f'hey ken! welcome back to cloudhouse!')
        user = 'Ken'

    if message.startswith('!cheap'):
        return {'webhook':'','message': flipper.togglemgr(user, message)}

    global chathistory
    # if !setcontext, set forcesubject
    if message.startswith('!setcontext'):
        #add all but !setcontext to forcesubject
        forcesubject = message[11:]
        print(f'forcesubject: {forcesubject}')

        return {'webhook':'','message':'forcesubject set'}
    
    #!clearhistory to clear chathistory. if integer specified, clear that many messages from start
    if message.startswith('!clearhistory'):
        if message == '!clearhistory':
            chathistory.clear()
            return {'webhook':'','message':'chathistory cleared'}
        else:
            try:
                num = int(message[14:])
                chathistory = chathistory[num:]
                return {'webhook':'','message':f'cleared {num} messages from chathistory'}
            except ValueError:
                return {'webhook':'','message':'invalid integer specified'}
    
    #if message starts with ! in general, skip adding to chathistory
    if message.startswith('!'):
        print('skipping history')
        skip_history = True

    #get datetime
    now = datetime.datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    #chathistory.append(f'[{timestamp}] {user}: {message}')
    chathistory.append(f'[{user}: {message}')
    print(f'debug chathistory: {chathistory}')

    # get webhook from either ari_webhooks or personality.pwhl
    all_webhooks = {**ari_webhooks.webhook_library, **personality.pwhl}
    try:
        webhook = all_webhooks[friend]
    except KeyError:
        # somebody tried to call a friend that doesn't exist :(
        friend = random.choice(members)
        webhook = all_webhooks[friend]
    username = webhook[0]
    #debug
    try:
        description = webhook[2]
    except IndexError:
        print(f'error getting description for {username}')
        description = ''
    prompt = f'{personality.cloudhouse_prompt2} information about your character and personality, {username} : {description}'
    if forcesubject:
        prompt = f'{prompt} subject of the message: {forcesubject}'
    print(prompt)
    # get message
    if not flipper.cheap:
        cmodel = 'claude-3-opus-20240229'
    else:
        cmodel = 'claude-3-haiku-20240307'
    print('chosen claudemodel:', cmodel)
    chresponse = await sentience.ch_claudex(prompt,chathistory,cmodel)

    #if first character is a *, regex everything until the next * and remove it
    if re.match(r'^\*',chresponse):
        chresponse = re.sub(r'^\*.*?\*', '', chresponse)

    #sometimes this responds with the username, if there is a : in the first word, regex to remove the first word
    if re.match(r'^\w+:',chresponse):
        chresponse = chresponse.split(':',1)[1]

    chathistory.append(f'{username}: {chresponse}')

    return {'webhook':webhook,'message':chresponse}


