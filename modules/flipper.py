zoomerposting = False
translation_enabled = False
current_model = "moonshotai/kimi-k2.5"
spotify_enable = True
cheap = True
precheck = False
auto_skeeter = 0
zp_last_msg_author = ''
zp_msg = ''

MODEL_HELP = """
Available models:
  moonshotai/kimi-k2.5  (default, reasoning disabled)
  anthropic/claude-sonnet-4-6
  anthropic/claude-3-5-haiku-latest
  openai/gpt-4o
"""

def togglemgr(user, message):
    global zoomerposting, translation_enabled, current_model, spotify_enable, cheap, precheck, auto_skeeter
    if message == '!zoomerposting':
        zoomerposting = not zoomerposting
        return f'zoomerposting is now {bool_to_str(zoomerposting)}'
    elif message == '!translation':
        translation_enabled = not translation_enabled
        return f'translation is now {bool_to_str(translation_enabled)}'
    elif message.startswith('!model'):
        parts = message.split(maxsplit=1)
        if len(parts) == 1:
            return f'Current model: {current_model}\n{MODEL_HELP}'
        new_model = parts[1].strip()
        current_model = new_model
        return f'Model changed to: {current_model}'
    elif message == '!spotify':
        spotify_enable = not spotify_enable
        return f'spotify is now {bool_to_str(spotify_enable)}'
    elif message == '!precheck':
        precheck = not precheck
        return f'precheck is now {bool_to_str(precheck)}'
    elif message.startswith('!autoskeeter'):
        parts = message.split()
        if len(parts) == 1:
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

def bool_to_str(bool):
    if bool:
        return 'enabled'
    else:
        return 'disabled'