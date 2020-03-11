from mastodon import Mastodon
import maricon

'''
Mastodon.create_app(
     'ari5',
     api_base_url = 'https://mastodon.social',
     to_file = 'ari5_clientcred.secret'
)
'''

mastodon = Mastodon(
    client_id = 'ari5_clientcred.secret',
    api_base_url = 'https://mastodon.social'
)
mastodon.log_in(
    maricon.mastouser,
    maricon.mastopassword,
    to_file = 'ari5_usercred.secret'
)


def tootcontrol(message):
    outputmsg = []
    print('tooting message {}'.format(message))
    ourtoot = mastodon.toot(message)
    outputmsg.append(ourtoot['url'])
    return outputmsg

