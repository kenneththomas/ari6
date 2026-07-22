import asyncio

from modules.context_tools import send_ai_response, split_discord_message
from modules.personas import Persona, persona_store


async def send_persona_response(
    channel,
    text,
    get_or_create_webhook,
    persona: Persona | None = None,
    multiline_threshold: int = 8,
    reply_to=None,
):
    """Send using the bot identity for Ari or a shared webhook for other personas."""
    persona = persona or persona_store.default()
    if persona.use_bot_identity:
        await send_ai_response(
            channel,
            text,
            multiline_threshold=multiline_threshold,
            reply_to=reply_to,
        )
        return

    try:
        webhook = await get_or_create_webhook(channel, "ari-personas")
        webhook_kwargs = persona.webhook_kwargs()
        if text.count("\n") < multiline_threshold:
            for line in text.split("\n"):
                for chunk in split_discord_message(line):
                    await asyncio.sleep(0.5)
                    await webhook.send(chunk, **webhook_kwargs)
        else:
            for chunk in split_discord_message(text):
                await webhook.send(chunk, **webhook_kwargs)
    except Exception as error:
        print(
            f"Could not post as persona {persona.key}; using bot identity: {error}"
        )
        await send_ai_response(
            channel,
            text,
            multiline_threshold=multiline_threshold,
            reply_to=reply_to,
        )
