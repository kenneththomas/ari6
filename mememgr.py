import random
from re import compile
import control

bgbscanner = compile(r'whos [a-z][a-z][a-z]$')
repeatercache = []

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

    return mememessages

def cleanup_username(name):
    if name.isalnum() == True:
        return name
    else:
        return 'badname'

def battlerap_cleanup(message):
    # a lot of the messages end in '\' because i imported it from text battle rap. simply remove that
    # might extend this to remove the CAPITAL LETTERS to EMPHASIZE RHYMES but i like that the way it is for now
    message = message.strip('\\')
    return message