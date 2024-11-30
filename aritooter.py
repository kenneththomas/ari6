from mastodon import Mastodon
import maricon
from atproto import Client
#import twitter

'''
Mastodon.create_app(
     'ari5',
     api_base_url = 'https://mastodon.social',
     to_file = 'ari5_clientcred.secret'
)
'''

# Initialize Bluesky client
bsky = Client()
# You'll need to login before posting
bsky.login(
    maricon.bskyuser,  # replace with your handle
    maricon.bskypass         # use an app-specific password from your Bluesky settings
)

def tootcontrol(message):
    outputmsg = []
    print('tooting message {}'.format(message))
    
    # Add Bluesky post
    try:
        bsky_post = bsky.send_post(text=message)
        outputmsg.append(f"https://bsky.app/profile/{bsky.me.did}/post/{bsky_post.uri.split('/')[-1]}")
    except Exception as e:
        print(f"Bluesky post failed: {e}")
    
    return outputmsg
