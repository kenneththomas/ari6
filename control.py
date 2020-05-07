#config
adminlist=['breezyexcursion#9570']
bannedwords = ['netorare']

def admincheck(user):
    if user in adminlist:
        print('Control: {} is authorized to run admin command'.format(user))
        return True
    else:
        print('Control: {} not authorized to run admin command'.format(user))
        return False

def bannedwordsmgr(message, author):
    class bwmpayload():
        delete = False
    bwm = bwmpayload()

    if message == '!bw list':
        print('BWM: received list request')
        bwm.message = 'Current words are banned: {}'.format(bannedwords)
        return bwm

    for bannedword in bannedwords:
        if bannedword in message:
            print('BWM: detected message with banned phrase {}'.format(bannedword))
            bwm.delete = True

    return bwm