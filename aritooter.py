from mastodon import Mastodon
import maricon
#import twitter

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

'''
twitterapi = twitter.Api(consumer_key=maricon.twitterconsumerkey,
                        consumer_secret=maricon.twitterconsumersecret,
                        access_token_key=maricon.twitteraccesstoken,
                        access_token_secret=maricon.twitteraccesstokensecret)
'''
