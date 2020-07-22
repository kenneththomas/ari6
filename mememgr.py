import random
from re import compile

bgbscanner = compile(r'whos [a-z][a-z][a-z]$')

def chance(x):
    saychance = random.randint(1,x)
    if saychance == 1:
        chancerespond = True
        print('MemeMgr: Memed with a chance of 1/' + str(x))
    else:
        chancerespond = False
    return chancerespond

def memes(message):

    mememessages=[] #contains all messages that mememgr will return

    if message == 'hi':
        if chance(6):
            mememessages.append('hi')

    if message == '+':
        if chance(6):
            mememessages.append('+')

    if message == 'a':
        if chance(7):
            mememessages.append('a')

    if message == 'push me to the edge':
        mememessages.append('all my friends are dead')

    if message == 'all my friends are dead':
        mememessages.append('push me to the edge')

    if 'how do you' in message:
        if chance(4):
            mememessages.append('very carefully!')


    if ' dn' in message:
        if message == 'whats dn' or message == 'what\'s dn':
            if chance(4):
                mememessages.append('deez nuts')
        else:
            if chance(11):
                mememessages.append('whats dn')

    bgbmatch = bgbscanner.search(message)
    if bgbmatch:
        response = message[5] + 'ill ' + message[6] + 'arls' + message[7] + 'y'
        print('MemeMgr: Found BGB Match')
        mememessages.append(response)

    #rare pepes
    if chance(99999):
        rarepicker = messagepicker(4)
        if rarepicker == 1:
            mememessages.append('zip zop')
        if rarepicker == 2:
            mememessages.append('smells like catupto in here')
        if rarepicker == 3:
            mememessages.append('hey evryone whatsup gamboys')
        if rarepicker == 4:
            mememessages.append('whats cat up to')

    if message.startswith("t!weather"):
        #dont do this if a zip code, emoji, or obvious nonlocation
        if message.split()[1].startswith('<'):
            print('this bad')
        try:
            int(message.split()[1])
        except ValueError:
            mememessages.append(message[10:] + " " + message[10] + 'ory')

    return mememessages

def cleanup_username(name):
    if name.isalnum() == True:
        return name
    else:
        return 'badname'