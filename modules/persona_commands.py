from __future__ import annotations

from modules.personas import Persona, PersonaStore, normalize_persona_key, persona_store


PERSONA_HELP = """Persona commands:
`!persona` - show the active persona
`!persona list` - list available personas
`!persona show <key>` - show persona details
`!persona use <key>` - select the default persona (admin)
`!persona add <key> | <name> | <prompt>` - add using an attached avatar (admin)
`!persona add <key> | <name> | <avatar URL> | <prompt>` - add using a URL (admin)
`!persona edit <key> | <name|avatar|prompt> | <value>` - edit (admin)
`!persona delete <key>` - delete or hide a persona (admin)
`!persona reset <key>` - restore a public built-in (admin)
"""


def _attachment_avatar(message) -> str:
    attachments = getattr(message, "attachments", [])
    return str(attachments[0].url) if attachments else ""


def _format_persona(persona: Persona, active_key: str) -> str:
    active = " (active)" if persona.key == active_key else ""
    identity = "bot identity" if persona.use_bot_identity else "webhook identity"
    avatar = persona.avatar_url or "bot avatar"
    prompt = persona.prompt
    if len(prompt) > 900:
        prompt = prompt[:897] + "..."
    return (
        f"**{persona.display_name}** (`{persona.key}`){active}\n"
        f"Identity: {identity}\nAvatar: {avatar}\nPrompt: {prompt}"
    )


async def handle_persona_command(
    message,
    is_admin: bool,
    store: PersonaStore = persona_store,
) -> bool:
    """Handle the lightweight, persistent Discord persona management UI."""
    content = str(message.content).strip()
    lowered_content = content.lower()
    if lowered_content != "!persona" and not lowered_content.startswith("!persona "):
        return False

    remainder = content[len("!persona") :].strip()
    if not remainder:
        await message.channel.send(
            _format_persona(store.default(), store.default_key) + "\n\n" + PERSONA_HELP
        )
        return True

    command, _, argument = remainder.partition(" ")
    command = command.lower()
    argument = argument.strip()

    if command == "list":
        entries = [
            f"{'→' if persona.key == store.default_key else '•'} "
            f"`{persona.key}` — {persona.display_name}"
            for persona in store.all()
        ]
        await message.channel.send("**Personas**\n" + "\n".join(entries))
        return True

    if command == "show":
        persona = store.get(argument or store.default_key)
        if persona is None:
            await message.channel.send(f"Unknown persona: `{argument}`")
        else:
            await message.channel.send(_format_persona(persona, store.default_key))
        return True

    if command == "help":
        await message.channel.send(PERSONA_HELP)
        return True

    if not is_admin:
        await message.channel.send("You do not have permission to change personas.")
        return True

    try:
        if command == "use":
            persona = store.set_default(argument)
            await message.channel.send(
                f"Default persona is now **{persona.display_name}** (`{persona.key}`)."
            )
        elif command == "add":
            fields = [field.strip() for field in argument.split("|")]
            attached_avatar = _attachment_avatar(message)
            if len(fields) == 3 and attached_avatar:
                key, display_name, prompt = fields
                avatar_url = attached_avatar
            elif len(fields) == 4:
                key, display_name, avatar_url, prompt = fields
            else:
                raise ValueError(
                    "Use `!persona add <key> | <name> | <prompt>` with an image "
                    "attachment, or include an avatar URL before the prompt."
                )
            normalized_key = normalize_persona_key(key)
            if store.get(normalized_key) is not None:
                raise ValueError(
                    f"Persona `{normalized_key}` already exists; use `!persona edit`."
                )
            persona = store.save(
                Persona(
                    key=normalized_key,
                    display_name=display_name,
                    avatar_url=avatar_url,
                    prompt=prompt,
                )
            )
            await message.channel.send(
                f"Saved **{persona.display_name}** as `{persona.key}`."
            )
        elif command == "edit":
            fields = [field.strip() for field in argument.split("|", maxsplit=2)]
            if len(fields) != 3:
                raise ValueError(
                    "Use `!persona edit <key> | <name|avatar|prompt> | <value>`."
                )
            key, field, value = fields
            if field.lower() in {"avatar", "avatar_url", "avatar-url"} and not value:
                value = _attachment_avatar(message)
            persona = store.update(key, field, value)
            await message.channel.send(f"Updated `{persona.key}`.")
        elif command in {"delete", "remove"}:
            store.delete(argument)
            await message.channel.send(f"Deleted persona `{normalize_persona_key(argument)}`.")
        elif command == "reset":
            persona = store.reset(argument)
            await message.channel.send(f"Reset `{persona.key}` to its public definition.")
        else:
            await message.channel.send(PERSONA_HELP)
    except (KeyError, ValueError, OSError) as error:
        await message.channel.send(f"Could not update persona: {error}")
    return True
