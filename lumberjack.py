from datetime import datetime
import mememgr
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

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
    logfix = '8=A6F;35=6L;49={};56={};52={};58={}'.format(sender,channel,timestamp,message)
    #print(logfix)
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

    return

def stats(maxusers=8):
    # Connect to your SQLite database
    conn = sqlite3.connect('logs/gato.db')

    # Read the data into a pandas DataFrame
    query = "SELECT sender, timestamp FROM logs"
    df = pd.read_sql_query(query, conn)

    # Close the SQLite connection
    conn.close()

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Group the data by sender and timestamp
    grouped_df = df.groupby([pd.Grouper(key='timestamp', freq='D'), 'sender']).size().reset_index(name='count')
    # Define a list of senders to exclude
    exclude_senders = ['breezbot']

    # Filter out the excluded senders
    filtered_df = grouped_df[~grouped_df['sender'].isin(exclude_senders)]

    # Get the top 6 senders by message count
    top_senders = filtered_df.groupby('sender')['count'].sum().sort_values(ascending=False).head(maxusers).index.tolist()

    # Assign an 'Other' category to the senders not in the top 6
    grouped_df['sender'] = grouped_df['sender'].apply(lambda x: x if x in top_senders else 'Other')

    # Pivot the data
    pivoted_df = grouped_df.pivot_table(values='count', index='timestamp', columns='sender', fill_value=0)

    # Set up seaborn style
    sns.set(style="whitegrid")

    # Create a stacked area chart
    plt.figure(figsize=(12, 6))
    ax = plt.gca()
    pivoted_df.plot.area(ax=ax, alpha=0.5)

    # Customize the chart
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Total Messages")
    ax.set_title("Messages over Time by Sender")
    ax.legend(title="Sender")

    # Save the chart as an image
    plt.savefig("tmp/stacked_area_chart.png", dpi=300)

    return 'tmp/stacked_area_chart.png'


