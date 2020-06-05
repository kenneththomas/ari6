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
        message = False
    bwm = bwmpayload()



    if message == '!bw list':
        print('BWM: received list request')
        bwm.message = 'Current words are banned: {}'.format(bannedwords)
        return bwm

    # admin controls
    if message.startswith('!'):
        if admincheck(author):
            if message.startswith('!bw add'):
                addword = message.split(' ')
                bannedwords.append(addword[2])
                print('BWM: added {} to the banned words list'.format(addword[2]))
                bwm.message = 'Added {} to the banned words list'.format(addword[2])
            if message.startswith('!bw remove'):
                removeword = message.split(' ')
                bannedwords.remove(removeword[2])
                print('BWM: removed {} from the banned words list'.format(removeword[2]))
                bwm.message = 'Removed {} from the banned words list'.format(removeword[2])
            return bwm

    for bannedword in bannedwords:
        if bannedword in message:
            print('BWM: detected message with banned phrase {}'.format(bannedword))
            bwm.delete = True

    return bwm