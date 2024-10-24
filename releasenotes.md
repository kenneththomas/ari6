# releasenotes

## 8.9
- this is crazy dude

## 8.8.14
- increase sleep time between messages
- xp logic cleanup
- trivia cleanup
- remove some unused sentience functions
- webhooks cleanup

## 8.8.13
- zithers rolled

## 8.8.12
- msg splitting

## 8.8.11
- claude version bump

## 8.8.10
- significantly reduce spotify roast frequency
- recommendations on what to eat (popsicle)

## 8.8.9.1
- sleep during updates to avoid rate limits
- remove trump getting shot context cuz bot wont stop talking about it

## 8.8.9
- experimental container memory management
- clip improvements

## 8.8.8.1
- specify which games are being updated, so we can differentiate if multiple games are being played

## 8.8.8
- allow use of !clip for clipping
- comment out im chras sc
- jane doe context
- rip dominican ari

## 8.8.7.2
- filter for maryland and texas a&m games only

## 8.8.7.1
- cfbscoreboard

## 8.8.7
- filter clip
- remove emoji storage as its not used anywhere
- disable random bot responses in joey for now

## 8.8.6
- post sample of clipped message and provide ability to confirm or deny

## 8.8.5
- clip previous x messages

## 8.8.4-hotfix
- needs to be exact match for chat clip this

## 8.8.4
- chat, is this rizz??
- chat clip this

## 8.8.3
- add hebrew to translation support

## 8.8.2
- fix case sensitivity in context

## 8.8.1
- polychrome

## 8.8
- context through csv file

## 8.7.5
- view_image in sentience
- update one of the 3.5-turbo to gpt-4o-mini that was missed in the last one
- rebrand "short_uuid" to "question_id"
- added joey module, eventually we will move all of the trivia stuff to this module
- add !triviahelp command


## 8.7.4
- replace gpt-3.5 with gpt-4o-mini
- reduce chance of bot response in who-is-joey

## 8.7.3
- use add_xp_user function in the basic post message award
- u cant do that lol
- free bot channel demo
- default main on

## 8.7.2
- top 10 xp

## 8.7.1
- remove claudex original function
- !np also shows nowplaying
- allow repeat functionality in masta_selecta

## 8.7
- default claude
- update claude messaging format so claude knows what it wrote vs what the chat wrote

## 8.6.14
- remove oldest 3 msgs from bot msg container if more than 2000 characters (commented out for now)
- move from claude 3 opus to claude 3.5 sonnet
- avoid greetings in claude

## 8.6.13
- reduce spotify roast chance from 1/5 to 1/10
- temporarily admincheck toot feature as its my personal account rn
- new !gpt4 to call gpt4o
- i think we dont need that timeout function anymore
- reduce max tokens on reply request from 800 to 300

## 8.6.12
- lamelo reacts to messages sometimes
- lamelo gets more context by combining msgs when same author posts more than once in a row
- use gpt-4o for zoomerposting messages
- fix bug where other websites ending in x.com (like complex.com) were trying to do the vxtwitter fix

## 8.6.11
- use gpt-o wherever gpt-4 turbo was being used before

## 8.6.10
- flipper returns enabled/disabled instead of True/False
- slightly reduce zoomerposting frequency

## 8.6.9
- bot roasts ur music taste

## 8.6.8
- gpt version bump to gpt-4-turbo-2024-04-09

## 8.6.7
- allow zoomer to post in other channels
- fix twitter posting to wrong channel

## 8.6.6
- clearhistory deletes from end instead of beginning, kinda like a retry feature
- cheap needed to be added to global
- zoomerposting prompt update
- zoomerposting only posts in barco, so display typing should only be in barco
- don't print the whole xp board on xp update

## 8.6.5
- adjust spotify ft placement
- remove newline when printing now playing in log
- add partial clear history to cloudhouse
- toggle opus/haiku in flipper
- use my name instead of my username for cloudhouse

## 8.6.4.1
- fix vxtwitter embed which was posting my messages to the wrong room

## 8.6.4
- spotify fix attributeerror when user is listening to a local song and artist is not accessible via API
- migrate spotify_enabled to flipper

## 8.6.3
- introduce flipper.py to eventually manage all of the toggles
- migrate zoomerposting to flipper
- migrate translation_enabled to flipper
- migrate claude to flipper

## 8.6.2
- like you're doing right now? (bok request)
- gonna start doing some cleanup i guess ari6.py is gettin spaghetti
- spotify sometimes the track already has features in the title, skip that if thats the case
- dont repeat album art that doesnt work, but i gave up for now its friday
- preload channels

## 8.6.1
- !spotify toggles now playing 
- if spotify song has multiple artists, make it look better

## 8.6
- old
- spotify now playing
- post album art as separate message so it doesnt show the link to the picture
- give 1xp for listening to music
- moved xp flush from 15 to 25
- print startup time (its about 2.5 seconds on my dev box rn)

## 8.6-alpha.2
- clear history

## 8.6-alpha.1
- cloudhouse single
- track date in cloudhouse single
- remove stupid claude action sht
- error handling if cloud doesnt return msg

## 8.6-alpha
- emojiserver hookup
- queued messages handling
- allow changing model in claude/gpt sentience functions
- fix emojiserver history
- emojiserver force subject
- delete message from sender if forcesubject was used

## 8.5.8
- cleanup reverse translation a little
- change language crosspost shortcut from xt to xx
- log deleted messages to console

## 8.5.8-beta
- fix do not translate from config channel
- tatsu bot commands no longer award xp (ex: t!weather)
- reverse translation (beta feature)

## 8.5.7
- get xp works for users other than self
- do not translate from config channel
- get nba scores with !ctespn (this will expand to more later)

## 8.5.6
- additional logging around flush to db
- "zoomerposting" functionality where bot will occasionally respond with short messages including a skull emoji
- add lamelo ball webhook
- generic gpt function has a default prompt in the function now but it can be overridden
- zoomerposting uses lamelo ball webhook

## 8.5.5-hotfix-xp
- fix keyerror for new users xp

## 8.5.5
- display channel on cli log
- do not store config channel messages in db
- emoji logging in cli, 1 xp for emoting

## 8.5.4
- refactor xp to fix database locking
- batchsize adjustment valdiation

## 8.5.3
- bot commands - do not save to log db or award xp
- reduce xp for getting a trivia question correct from 10 to 3
- trivia hints
- trivia gets its own dedicated gpt function instead of reusing spanish, it uses gpt4 and has a lower token limit
- rename some of the spanish stuff to translation stuff cuz it does more than just spanish
- toggle main adjustment

## 8.5.2
- bot appears to be typing while doing trivia ai stuff
- remove the aggregation stuff
- functionality to add trivia questions
- save trivia questions
- allow adjusting of log batching
- partial trivia answer handling but commented out for now

## 8.5.1
- !xp tells you how much xp you have
- add_xp_user lets u add xp to a user
- trivia with hosting

## 8.5
- xp implementation