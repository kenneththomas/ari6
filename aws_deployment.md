AWS Deployment Notes
I fried the SD card on my raspberry pi probably from logging a billion times to it. Log to external storage next time. Lesson learned.

Temporarily (or maybe permanently) migrating to AWS

how to connect to aws:
/home/kenneth/howtoconnect.txt

yum package installer
python3.11
pip3.11

maricon.py gitignored because it has keys
gpt key
discord bot key

Built-in bot personas are versioned in `resources/personas.json`. Discord-created
persona overrides and the selected default live in the gitignored
`resources/personas_state.json`; preserve that file when replacing a deployment.

The old `personality.py` is private legacy data and is not loaded by the bot.

install Python dependencies with `python -m pip install -r requirements.txt`

set `OPENROUTER_API_KEY` in the service environment, or set `openrouter_key` in
the gitignored `maricon.py` file

thats it, its running already!

Bluesky enable instructions:
install with `python -m pip install -r requirements_bluesky.txt`
add `bskyuser` and `bskypass` to the local credential module
the Bluesky client logs in lazily on the first posting attempt

log db:
/home/ec2-user/prod/ari6/logs/gato.db
