import markovify
import mememgr as mm
import datetime

print('initializing sentience...')
with open('logs/everyone.log') as jtxt:
    text = jtxt.read()

#print number of lines in the log
print('number of lines in the log: {}'.format(len(text.splitlines())))

#get the current time to check how long it takes to load text
starttime = datetime.datetime.now()
text_model = markovify.NewlineText(text)
endtime = datetime.datetime.now()
print('time to load text: {}'.format(endtime - starttime))

def genmsg():
    basemessage = text_model.make_short_sentence(140)
    finalmessage = mm.battlerap_cleanup(basemessage)
    return finalmessage