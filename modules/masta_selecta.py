songlibrary = {}

def nowplaying(user, songinfo):
    features = None


    artist = str(songinfo.artist)
    

    if ';' in artist:
        #spotify separates multiple artists for a song with ; which looks stupid
        multiple_artists = artist.split(';')
        song_artist = multiple_artists[0]
        features = multiple_artists[1:]
    else:
        song_artist = artist

    npstring = f'{song_artist} - {songinfo.title}\n{songinfo.album}'

    if features:
        # sometimes the track name already has the featured artist in it, in that case we dont need to repeat it
        if features[0] in songinfo.title:
            features = None
            print('features already in title! not adding')
        else:
            npstring += f' (ft. {",".join(features)})'

    albumart = songinfo.album_cover_url

    # do not repeat album art - this isnt working
    try:
        print(f'{songinfo.album} == {songlibrary[user]}')
        oldtrack = songlibrary[user]
        if str({songinfo.album}) in str(oldtrack):
            print('album is the same as the last one so we dont need to post it')
            albumart = None
    except KeyError:
        pass

    if user not in songlibrary.keys() or npstring != songlibrary[user]:
        songlibrary[user] = npstring
        return (npstring, albumart)
    else:
        return None, None