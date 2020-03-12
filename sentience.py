import markovify

with open('logs/everyone.log') as jtxt:
    text = jtxt.read()

jesus_text_model = markovify.NewlineText(text)

def genmsg():
    return jesus_text_model.make_short_sentence(140)