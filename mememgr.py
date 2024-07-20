import random
from re import compile
import control
import datetime

bgbscanner = compile(r'whos [a-z][a-z][a-z]$')
repeatercache = []
onlyonce = []

def chance(x):
    saychance = random.randint(1,x)
    if saychance == 1:
        chancerespond = True
        print('MemeMgr: Memed with a chance of 1/' + str(x))
    else:
        chancerespond = False
    return chancerespond

def repeater(message):
    global repeatercache
    if message not in repeatercache:
        repeatercache = []
        repeatercache.append(message)
        return False
    else:
        print('repeater: detected repeat message!')
        repeatercache.append(message)
        if len(repeatercache) > 3:
            print('repeater: more than 3 repeated messages! {}'.format(message))
            repeatercache = []
            # defensive code against bari
            for bannedword in control.bannedwords:
                if bannedword in message:
                    print('mememgr: not repeating because there is a banned word in the message')
                    return False
            return True
        else:
            return False

def meme_loader():

    print('initializing meme loader')
    #memebox will be populated with the content of resources/memes.csv and returned for mememgr to load memes
    global memebox
    memebox = {}
    memefile = open('resources/memes.csv')
    memedata = memefile.readlines()
    
    for meme in memedata:
        
        memesplit = meme.split(',')
        #do not use header
        if memesplit[0] == 'trigger':
            continue
        memebox[memesplit[0]] = memesplit

    memefile.close()
    
    return memebox

    
def memes(message):
    
    mememessages=[] #contains all messages that mememgr will return

    if repeater(message):
        if message.startswith('huh'):
            mememessages.append('like you\'re doing right now?')
        else:
            mememessages.append(message)

    #memebox functionality
    if message in memebox.keys():
        response = memebox[message][1].rstrip()
        chancevalue = memebox[message][2]

        if chance(int(chancevalue)):
            mememessages.append(response)

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

    if message.startswith("t!weather"):
        #dont do this if a zip code, emoji, or obvious nonlocation
        if message.split()[1].startswith('<'):
            print('this bad')
        try:
            int(message.split()[1])
        except ValueError:
            mememessages.append(message[10:] + " " + message[10] + 'ory')

    #if message starts with !spongebob
    if message.startswith('!spongebob'):
        #randomly capitalize letters in the message and add it to mememessages
        message = message.replace('!spongebob ','')
        mememessages.append(spongemock(message))        

    return mememessages

def spongemock(msg):
    return ''.join([ch.lower() if ch.isalpha() and len([c for c in msg[:i] if c.isalpha()]) % 2 else ch for i, ch in enumerate(msg.upper())])

def cleanup_username(name):
    if name.isalnum() == True:
        return name
    # if the name is not alphanumeric, remove all non-alphanumeric characters
    else:
        name = ''.join(e for e in name if e.isalnum())
        return name

def battlerap_cleanup(message):
    # a lot of the messages end in '\' because i imported it from text battle rap. simply remove that
    # might extend this to remove the CAPITAL LETTERS to EMPHASIZE RHYMES but i like that the way it is for now
    message = message.strip('\\')
    return message


def emoji_reactor(message,author):
    emojilist = []
    # this function will return a list of emojis to react with
    if message == 'bari':
        if chance(10):
            emojilist.append('😳')
            emojilist.append('👋')
    # if the message starts with anyone, 20% chance to add the u emoji to the list
    if message.startswith('anyone'):
        if chance(5):
            emojilist.append('🇺')
    # if the message starts with unittest testcase add the check emoji to the list
    if message.startswith('unittest testcase'):
        emojilist.append('✅')

    '''
    # if the user that sent the message is soup, react with coconut emoji and palm tree emoji one time
    if 'soup' in author:
        if 'soup' not in onlyonce:
            emojilist.append('🥥')
            emojilist.append('🌴')
            onlyonce.append('soup')
    '''
    
    if 'breez' in author:
        # if the message has more than 110 characters and ends in punctuation, react with the heart emoji
        if len(message) > 110 and message[-1] in ['.', '!', '?']:
            print('heart react disabled')
            #emojilist.append('❤️')
            
    return emojilist