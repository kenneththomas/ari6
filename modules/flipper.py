zoomerposting = False
translation_enabled = False
claude = False

def togglemgr(user, message):
    global zoomerposting, translation_enabled, claude
    if message == '!zoomerposting':
        zoomerposting = not zoomerposting
        return f'zoomerposting is now {zoomerposting}'
    elif message == '!translation':
        translation_enabled = not translation_enabled
        return f'translation is now {translation_enabled}'
    elif message == '!claude':
        claude = not claude
        return f'claude is now {claude}'
