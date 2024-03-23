import ari_webhooks
import random
import sentience
import personality
import re

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

