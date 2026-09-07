import discord
import lumberjack as l
import mememgr
import sentience
from modules.personas import persona_store

songlibrary = {}


def _spotify_activity(activities):
    """Return Discord's Spotify activity, if the member exposes one."""
    for activity in activities or ():
        if isinstance(activity, discord.Spotify):
            return activity
        # Keep compatibility with activity-like objects from older caches/tests.
        if (
            getattr(activity, 'type', None) == discord.ActivityType.listening
            and getattr(activity, 'name', None) == 'Spotify'
        ):
            return activity
    return None

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
    is_np_command = message.content.strip().lower() == '!np'
    activity = _spotify_activity(getattr(message.author, 'activities', ()))

    if activity is None:
        if is_np_command:
            await message.channel.send(
                "I can't see a current Spotify song for you. Make sure Spotify "
                "is connected to Discord and 'Display Spotify as your status' is enabled."
            )
            return True
        return False

    npstring, albumart = nowplaying(
        str(message.author),
        activity,
        allowrepeat=is_np_command,
    )
    if not npstring:
        if is_np_command:
            await message.channel.send(
                "I can see Spotify, but Discord isn't exposing track details. "
                "This can happen with a local track or an ad."
            )
            return True
        return False

    l.add_xp_user(str(message.author), 1)
    barco_webhook = None

    if is_np_command:
        await message.channel.send(npstring)
        if albumart:
            await message.channel.send(albumart)
    else:
        barco_webhook = await get_or_create_webhook(barcochannel, 'barco')
        avatar_url = str(message.author.display_avatar.url)
        await barco_webhook.send(
            npstring,
            username=message.author.display_name,
            avatar_url=avatar_url,
        )
        if albumart:
            await barco_webhook.send(
                albumart,
                username=message.author.display_name,
                avatar_url=avatar_url,
            )

    # Roast user's music taste with 40% chance
    if mememgr.chance(40):
        if barco_webhook is None:
            barco_webhook = await get_or_create_webhook(barcochannel, 'barco')
        roast_prompt = f'{message.author.display_name} is listening to {npstring}, roast them for it. you can comment negative things about the artist or make fun of particular lyrics from that song. end with a skull emoji.'
        roast = await sentience.generate_text(
            roast_prompt,
            gmodel=sentience.DEFAULT_TEXT_MODEL,
        )
        # Post as lamelo ball webhook
        persona = persona_store.get("lamelo-ball") or persona_store.default()
        await barco_webhook.send(
            roast,
            **persona.webhook_kwargs(),
        )

    return True
