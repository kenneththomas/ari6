from datetime import datetime, timedelta
import mememgr
import os
import sqlite3

# Configuration for batching
BATCH_SIZE = 15  # Number of messages to accumulate before writing to the database
FLUSH_INTERVAL = timedelta(minutes=5)  # Time to wait before flushing to the database

# Initialize
dbfilename = 'logs/gato.db'
batch_buffer = []
last_write_time = datetime.now()
xp_buffer = {}
trivia_questions = {}
newquestion = {}
questions_to_save = {}
previous_xp_buffer = {}

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Ensure the database and table exist
conn = sqlite3.connect(dbfilename)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS logs (sender text, channel text, timestamp text, date text, hour text, message text)''')
# create xp table
c.execute('''CREATE TABLE IF NOT EXISTS xp (user text, xp integer)''')
# populate xp buffer
c.execute("SELECT * FROM xp")
result = c.fetchall()
for row in result:
    xp_buffer[row[0]] = row[1]
# we use previous xp buffer to track changes to xp_buffer
previous_xp_buffer = xp_buffer.copy()
# create trivia_questions table
c.execute('''CREATE TABLE IF NOT EXISTS trivia_questions (question text, answer text)''')
# load trivia questions into memory, if there are no questions, add a sample one
c.execute("SELECT * FROM trivia_questions")
result = c.fetchall()
if not result:
    c.execute("INSERT INTO trivia_questions VALUES (?,?)", ('What is the capital of France?', 'Paris'))
    conn.commit()
    c.execute("SELECT * FROM trivia_questions")
    result = c.fetchall()
for row in result:
    trivia_questions[row[0]] = row[1]
conn.commit()
conn.close()

def flush_to_db():
    print('Flushing to database')
    global batch_buffer, last_write_time, xp_buffer, questions_to_save
    if not batch_buffer:
        return

    conn = sqlite3.connect(dbfilename)
    c = conn.cursor()
    c.executemany("INSERT INTO logs VALUES (?,?,?,?,?,?)", batch_buffer)
    print(f'xp updates: {xp_buffer}')

    for user, xp in xp_buffer.items():
        #check if xp has changed. if it has print the change and update the database
        try:
            if xp != previous_xp_buffer[user]:
                print(f'XP change for {user}: {previous_xp_buffer[user]} -> {xp}')
                c.execute("INSERT OR REPLACE INTO xp VALUES (?,?)", (user, xp))
                previous_xp_buffer[user] = xp
        except KeyError:
            print(f'XP change for {user}: 0 -> {xp}')
            c.execute("INSERT OR REPLACE INTO xp VALUES (?,?)", (user, xp))
            previous_xp_buffer[user] = xp
    #save trivia questions
    for question, answer in questions_to_save.items():
        print(f'Saving trivia question: {question} {answer}')
        c.execute("INSERT OR REPLACE INTO trivia_questions VALUES (?,?)", (question, answer))
    #reset questions_to_save
    questions_to_save = {}
    conn.commit()
    conn.close()
    
    # Clear the buffer and reset the last write time
    batch_buffer = []
    last_write_time = datetime.now()

def log(msg):
    global last_write_time
    now = datetime.now()
    
    # Process the message
    sender = mememgr.cleanup_username(str(msg.author.name))
    message = str(msg.content)
    channel = str(msg.channel)
    timestamp = str(now)
    date = timestamp.split(' ')[0]
    hour = timestamp.split(' ')[1].split(':')[0]

    newlog = f'[{timestamp}] ({channel}) {sender}: {message}'
    print(newlog)
    
    # no further processing on bot commands
    if message.startswith('!') or message.startswith('t!'):
        return
    
    # ignore config channel
    if channel == 'config':
        return

    # Add to batch buffer
    batch_buffer.append((sender, channel, timestamp, date, hour, message))

    # if sender not in xp_buffer, see if they are in the xp table and add to buffer
    if sender not in xp_buffer:
        print(f'Checking for XP for {sender}')
        conn = sqlite3.connect(dbfilename)
        c = conn.cursor()
        c.execute("SELECT xp FROM xp WHERE user = ?", (sender,))
        result = c.fetchone()
        if result:
            xp_buffer[sender] = result[0]
        else:
            print(f'No XP found for {sender}, adding to buffer')
            xp_buffer[sender] = 0
        conn.close()

    # add 1 xp to the sender
    # TODO: add a way to adjust xp gain
    xp_buffer[sender] += 1
    
    # Check if it's time to flush the buffer
    if len(batch_buffer) >= BATCH_SIZE or (now - last_write_time) >= FLUSH_INTERVAL:
        print(f'batch_buffer length: {len(batch_buffer)}, time since last write: {now - last_write_time}')
        flush_to_db()

def get_xp_user(user):
    #check buffer first
    if user in xp_buffer:
        return xp_buffer[user]
    else:
        return 0
    
def add_xp_user(user, xp):
    #check buffer first
    if user in xp_buffer:
        xp_buffer[user] += xp
        return