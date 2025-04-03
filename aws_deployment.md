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

personality.py gitignored because it has personal information

python modules needed (should i create a proper dependencies?)
discord
openai
Mastodon.py
atproto
anthropic
ptyz

thats it, its running already!

tooter enable instructions
even tho python module is called mastodon, you pip install "Mastodon.py"
add username (email) and password to maricon, uncomment top section to generate keys
re-comment after

log db:
/home/ec2-user/prod/ari6/logs/gato.db