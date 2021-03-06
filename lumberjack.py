from datetime import datetime
import mememgr

#########
# Logging model based off of FIX 4.2 Protocol
# Full Dictionary: https://www.onixs.biz/fix-dictionary/4.2/fields_by_tag.html
# Will try to keep usage of tags documented here though
#
# 8 = FIX Version
#
# 35 = Message Type
# 49 = Discord Account
# 52 = Timestamp
# 56 = Channel
# 58 = Message Text
#
#
#########

logfilename = 'logs/a5lfix.log'
logfile = open(logfilename, 'a')

def log(msg):
    sender = mememgr.cleanup_username(str(msg.author.name))
    message = str(msg.content)
    channel = str(msg.channel)
    timestamp = str(datetime.now())
    logfix = '8=A6F;35=6L;49={};56={};52={};58={}'.format(sender,channel,timestamp,message)
    print(logfix)
    logfile.write(logfix + '\n')
    logfile.flush()
    return
