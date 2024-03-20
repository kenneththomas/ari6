# releasenotes
making a releasenotes file because it is cute. no guarantees that i maintain this at all. use commit history lol

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