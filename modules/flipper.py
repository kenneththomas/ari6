zoomerposting = False
translation_enabled = False
claude = False
spotify_enable = True
cheap = True
zp_last_msg_author = ''
zp_msg = ''

def togglemgr(user, message):
    global zoomerposting, translation_enabled, claude, spotify_enable, cheap
    if message == '!zoomerposting':
        zoomerposting = not zoomerposting
        return f'zoomerposting is now {bool_to_str(zoomerposting)}'
    elif message == '!translation':
        translation_enabled = not translation_enabled
        return f'translation is now {bool_to_str(translation_enabled)}'
    elif message == '!claude':
        claude = not claude
        return f'claude is now {bool_to_str(claude)}'
    elif message == '!spotify':
        spotify_enable = not spotify_enable
        return f'spotify is now {bool_to_str(spotify_enable)}'

def chctl(user, message):
    global cheap
    if message == '!cheap':
        cheap = not cheap
        return f'cheap is now {cheap}'
    else:
        return '???'
    
#simple function to change true or false booleans to enabled or disabled string
def bool_to_str(bool):
    if bool:
        return 'enabled'
    else:
        return 'disabled'
    
