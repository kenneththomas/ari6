import markovify
import mememgr as mm

with open('logs/everyone.log') as jtxt:
    text = jtxt.read()

text_model = markovify.NewlineText(text)

def genmsg():
    basemessage = text_model.make_short_sentence(140)
    finalmessage = mm.battlerap_cleanup(basemessage)
    return finalmessage