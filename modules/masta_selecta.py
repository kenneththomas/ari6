import discord
import asyncio
import random
import lumberjack as l
import mememgr
import sentience
import ari_webhooks as wl

songlibrary = {}

def nowplaying(user, songinfo, allowrepeat=False):
    features = None

    try:
        artist = str(songinfo.artist)
    except AttributeError:
        print('masta_selecta: activity is spotify, but no artist found. probably a local track or ad. skipping.')
        return None, None
    

    if ';' in artist:
        #spotify separates multiple artists for a song with ; which looks stupid
        multiple_artists = artist.split(';')
        song_artist = multiple_artists[0]
        features = multiple_artists[1:]
    else:
        song_artist = artist

    npstring = f'{song_artist} - {songinfo.title}'

    if features:
        # sometimes the track name already has the featured artist in it, in that case we dont need to repeat it
        if features[0] in songinfo.title:
            features = None
            print('features already in title! not adding')
        else:
            npstring += f' (ft. {",".join(features)})'

    albumart = songinfo.album_cover_url

    npstring = npstring + f'\n({songinfo.album})'
    print(f'masta_selecta: {user} is listening to {npstring}'.replace('\n',' '))

    # do not repeat album art - this isnt working
    try:
        oldtrack = songlibrary[user]
        if str({songinfo.album}) in str(oldtrack):
            print('album is the same as the last one so we dont need to post it')
            albumart = None
    except KeyError:
        pass

    if user not in songlibrary.keys() or npstring != songlibrary[user]:
        songlibrary[user] = npstring
        return (npstring, albumart)
    elif allowrepeat:
        return (npstring, albumart)
    else:
        return None, None

async def handle_spotify_activity(message, get_or_create_webhook, barcochannel):
    """Handle Spotify activity detection and posting"""
    if not message.author.activities:
        return False
    
    for activity in message.author.activities:
        if activity.type == discord.ActivityType.listening and activity.name == 'Spotify':
            barco_webhook = await get_or_create_webhook(barcochannel, 'barco')
            npstring, albumart = nowplaying(str(message.author), activity)
            
            # Handle !np command with allowrepeat
            if message.content == '!np':
                npstring, albumart = nowplaying(str(message.author), activity, allowrepeat=True)
            
            if npstring:
                l.add_xp_user(str(message.author), 1)
                
                # Send to channel or webhook based on command
                if message.content == '!np':
                    await message.channel.send(npstring)
                    if albumart:
                        await message.channel.send(albumart)
                else:
                    await barco_webhook.send(npstring, username=message.author.name, avatar_url=message.author.avatar)
                    if albumart:
                        await barco_webhook.send(albumart, username=message.author.name, avatar_url=message.author.avatar)

                # Roast user's music taste with 40% chance
                if mememgr.chance(40):
                    roast_prompt = f'{message.author.display_name} is listening to {npstring}, roast them for it. you can comment negative things about the artist or make fun of particular lyrics from that song. end with a skull emoji.'
                    roast = await sentience.generate_text_gpt(roast_prompt, gmodel='gpt-4o')
                    # Post as lamelo ball webhook
                    await barco_webhook.send(roast, username='lamelo ball', avatar_url=wl.webhook_library['lamelo ball'][1])
                
                return True
    
    return False