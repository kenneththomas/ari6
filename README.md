# ari

## Description

ari is a versatile discord bot designed to enhance community interaction through a wide range of features including automated moderation, custom responses, language translation, meme generation, and social media integration. Built with Python and integrating various APIs, ari aims to provide an engaging and seamless experience for the dogs that inhabit gato.

## Local setup

Create and activate a virtual environment from the repo root:

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Unix/macOS/Linux:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Set an OpenRouter API key before starting the bot:

```powershell
$env:OPENROUTER_API_KEY = "your-key"
```

```sh
export OPENROUTER_API_KEY="your-key"
```

For the existing personal deployment, `openrouter_key` in the gitignored
`maricon.py` file is also supported.

Run the main bot:

```sh
python ari6.py
```

Bluesky posting is optional. To enable it, install its extra dependency and
provide `bskyuser` and `bskypass` in the existing local credential module:

```sh
python -m pip install -r requirements_bluesky.txt
```

## Features

- **Custom Commands:** React to specific commands with custom text responses, memes, or actions.
- **Social Media Link Handling:** Automatically modify or respond to social media links for optimized sharing within Discord.
- **Language Translation:** Support for multiple languages, allowing users to communicate more freely in their preferred language.
- **Moderation Tools:** Automated responses to banned words and the ability to manage messages and interactions.
- **Interactive Responses:** Engage with users through AI-driven text generation for replies, making conversations more lively.
- **Emoji Reactions:** Automatically react to certain messages with emojis to enhance interaction.
- **Webhook Integration:** Use webhooks for advanced message handling and custom notifications.

## Contributing

This bot is meant for my personal use and not for other discords but feel free to repurpose it for yours.
