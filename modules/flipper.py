zoomerposting = False
translation_enabled = False
claude = True
spotify_enable = True
cheap = True
precheck = False
auto_skeeter = 0
tk_thinking = True  # Controls the "thinking about TK" feature
zp_last_msg_author = ''
zp_msg = ''

def togglemgr(user, message):
    global zoomerposting, translation_enabled, claude, spotify_enable, cheap, precheck, auto_skeeter, tk_thinking
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
    elif message == '!precheck':
        precheck = not precheck
        return f'precheck is now {bool_to_str(precheck)}'
    elif message == '!tktoggle':
        tk_thinking = not tk_thinking
        return f'tk thinking is now {bool_to_str(tk_thinking)}'
    elif message.startswith('!autoskeeter'):
        parts = message.split()
        if len(parts) == 1:  # Just !autoskeeter with no number
            auto_skeeter = 0
            return 'auto skeeter is now disabled'
        try:
            chance = int(parts[1])
            auto_skeeter = chance
            return f'auto skeeter chance is now 1/{chance}'
        except ValueError:
            return 'Invalid chance value. Please use a number.'

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
    
