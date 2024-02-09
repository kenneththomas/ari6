from datetime import datetime
import mememgr
import os
import sqlite3
import json

dbfilename = 'logs/gato.db'
last15 = []

try:
    dbfile = open(dbfilename, 'a')
except FileNotFoundError:
    print('no dbfile found, creating new one')
    os.makedirs('logs', exist_ok=True)
    dbfile = open(dbfilename, 'w')

#create table in db if it doesnt exist - logs, contains columns, sender, channel, timestamp, date, hour, message
conn = sqlite3.connect(dbfilename)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS logs (sender text, channel text, timestamp text, date text, hour text, message text)''')

#close db
conn.commit()
conn.close()

def log(msg):
    sender = mememgr.cleanup_username(str(msg.author.name))
    message = str(msg.content)
    channel = str(msg.channel)
    timestamp = str(datetime.now())
    newlog = f'[{timestamp}] {sender}: {message}'
    print(newlog)
    #store last 15 messages
    last15.append(newlog)
    if len(last15) > 15:
        last15.pop(0)

    #example timestamp 2023-03-20 22:57:06.370854 get date and hour
    date = timestamp.split(' ')[0]
    hour = timestamp.split(' ')[1].split(':')[0]

    #write to db
    conn = sqlite3.connect(dbfilename)
    c = conn.cursor()
    c.execute("INSERT INTO logs VALUES (?,?,?,?,?,?)", (sender,channel,timestamp,date,hour,message))
    conn.commit()
    conn.close()

    #temporary write to json username, timestamp, message

    #convert timestamp to this format 2023-10-25 15:59:00

    #we only want to write to the json in the message has more than 15 characters
    if len(message) > 20 and len(message) < 200:
        timestamp = timestamp.split('.')[0]
        jsonfile = open('logs/log.json', 'a')
        json.dump({'username': sender, 'timestamp': timestamp, 'text': message}, jsonfile)
        jsonfile.write(',\n')
        jsonfile.close()

    return


