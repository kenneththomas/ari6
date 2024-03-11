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

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Ensure the database and table exist
conn = sqlite3.connect(dbfilename)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS logs (sender text, channel text, timestamp text, date text, hour text, message text)''')
conn.commit()
conn.close()

def flush_to_db():
    """Flush the batch buffer to the database."""
    print('Flushing to database')
    global batch_buffer, last_write_time
    if not batch_buffer:
        return

    conn = sqlite3.connect(dbfilename)
    c = conn.cursor()
    c.executemany("INSERT INTO logs VALUES (?,?,?,?,?,?)", batch_buffer)
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

    newlog = f'[{timestamp}] {sender}: {message}'
    print(newlog)
    
    # Add to batch buffer
    batch_buffer.append((sender, channel, timestamp, date, hour, message))
    
    # Check if it's time to flush the buffer
    if len(batch_buffer) >= BATCH_SIZE or (now - last_write_time) >= FLUSH_INTERVAL:
        flush_to_db()