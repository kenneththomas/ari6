import ari_webhooks
import random
import sentience
import personality

#object that we return, has webhook and message

members = personality.members
mainchars = personality.mainchars
chathistory = []

async def cloudhouse(user, message, replyto=None):
    chathistory.append(f'{user}: {message}')
    print(f'debug chathistory: {chathistory}')
    # select random member of cloudhouse
    #can call a specific friend with --friendname
    if '--' in message:
        friend = message.split()[0][2:]
        #strip the friendname from the message
        message = ' '.join(message.split()[1:])
        print(f'calling a specific friend: {friend}')
    else:
        friend = random.choice(members)
    # get webhook from either ari_webhooks or personality.pwhl
    all_webhooks = {**ari_webhooks.webhook_library, **personality.pwhl}
    try:
        webhook = all_webhooks[friend]
    except KeyError:
        # somebody tried to call a friend that doesn't exist :(
        friend = random.choice(members)
        webhook = all_webhooks[friend]
    username = webhook[0]
    description = webhook[2]
    prompt = f'{personality.cloudhouse_prompt} information about your character and personality, {username} : {description}'
    print(prompt)
    # get message
    if friend in mainchars:
        chresponse = await sentience.ch_claudex(prompt,chathistory)
    else:
        #turn chathistory into a string
        chstring = ' '.join(chathistory)
        chresponse = await sentience.generate_text_gpt(chstring,prompt)

    #sometimes this responds with the username:, strip it if it is there
    if chresponse.startswith(f'{username}:'):
        chresponse = chresponse[len(f'{username}:')+1:]

    chathistory.append(f'{username}: {message}')

    return {'webhook':webhook,'message':chresponse}

