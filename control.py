#config
adminlist=['breezyexcursion#9570']
bannedwords = ['netorare','periodt']
heldmsgcontainer = []

def admincheck(user):
    if user in adminlist:
        print('Control: {} is authorized to run admin command'.format(user))
        return True
    else:
        print('Control: {} not authorized to run admin command'.format(user))
        return False

def controlmgr(message, author):
    class bwmpayload():
        delete = False
        message = False
    class heldmessage():
        author = False
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
            elif message.startswith('!bw remove'):
                removeword = message.split(' ')
                bannedwords.remove(removeword[2])
                print('BWM: removed {} from the banned words list'.format(removeword[2]))
                bwm.message = 'Removed {} from the banned words list'.format(removeword[2])
            elif message.startswith('!admin add'):
                adduser = message.split(' ')
                adminlist.append(adduser[2])
                bwm.message = 'Added {} to admin list'.format(adduser[2])
            elif message.startswith('!admin remove'):
                removeuser = message.split(' ')
                adminlist.remove(removeuser[2])
                bwm.message = 'Removed {} from admin list.'.format(adduser[2])
            elif message == '!release':
                released = ''
                for x in heldmsgcontainer:
                    released = released + '{}: {}'.format(x.author,x.message)
                    if not bwm.message:
                        bwm.message = released + '\n'
                    else:
                        bwm.message = bwm.message + released + '\n'
                    heldmsgcontainer.remove(x)
            return bwm

    for bannedword in bannedwords:
        if bannedword in message:
            print('BWM: detected message with banned phrase {}'.format(bannedword))
            held = heldmessage()
            held.author = author
            held.message = message
            heldmsgcontainer.append(held)
            bwm.delete = True

    return bwm