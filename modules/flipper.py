zoomerposting = False
translation_enabled = False
claude = False
spotify_enable = True

def togglemgr(user, message):
    global zoomerposting, translation_enabled, claude, spotify_enable
    if message == '!zoomerposting':
        zoomerposting = not zoomerposting
        return f'zoomerposting is now {zoomerposting}'
    elif message == '!translation':
        translation_enabled = not translation_enabled
        return f'translation is now {translation_enabled}'
    elif message == '!claude':
        claude = not claude
        return f'claude is now {claude}'
    elif message == '!spotify':
        spotify_enable = not spotify_enable
        return f'spotify is now {spotify_enable}'
    
