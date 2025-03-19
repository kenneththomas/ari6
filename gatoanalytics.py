from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time
import random
import os
import sqlite3
from datetime import datetime
import discord
import maricon

# ----------------------------
# Flask and SocketIO Setup
# ----------------------------

# Create Flask app and configure SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# In-memory analytics data (now populated from database)
metrics = {
    'total_messages': 0,
    'total_reactions': 0,
    'active_users': 0
}

def update_metrics():
    """
    This background thread updates analytics from the database.
    """
    while True:
        # Get total messages from database
        db_cursor.execute("SELECT COUNT(*) FROM messages")
        metrics['total_messages'] = db_cursor.fetchone()[0]
        
        # Get active users (unique users in the last 10 minutes)
        ten_min_ago = (datetime.now().isoformat()[:-3])  # Current time minus 10 minutes
        db_cursor.execute("""
            SELECT COUNT(DISTINCT user) FROM messages 
            WHERE timestamp > datetime('now', '-10 minutes')
        """)
        metrics['active_users'] = db_cursor.fetchone()[0]
        
        # For reactions, we would need a reactions table
        # For now, keeping the simulated data for this metric
        metrics['total_reactions'] += random.randint(0, 3)
        
        # Get message count data for the last 10 minutes (for the chart)
        db_cursor.execute("""
            SELECT strftime('%Y-%m-%dT%H:%M:%S', timestamp) as minute, 
                   COUNT(*) as count 
            FROM messages 
            WHERE timestamp > datetime('now', '-10 minutes')
            GROUP BY strftime('%Y-%m-%dT%H:%M:00', timestamp)
            ORDER BY minute
        """)
        message_history = db_cursor.fetchall()
        
        # Emit the updated metrics to all connected clients
        socketio.emit('metrics_update', {
            'total_messages': metrics['total_messages'],
            'total_reactions': metrics['total_reactions'],
            'active_users': metrics['active_users'],
            'message_history': message_history
        })
        
        time.sleep(5)  # Update every 5 seconds - a reasonable interval

@app.route('/')
def index():
    """
    Serves the realtime dashboard page.
    """
    return render_template('index.html')

# ----------------------------
# SQLite Database Setup
# ----------------------------

# Ensure the logs directory exists.
if not os.path.exists('logs'):
    os.makedirs('logs')

# Connect to (or create) the SQLite database.
db_conn = sqlite3.connect('logs/analytics.db', check_same_thread=False)
db_cursor = db_conn.cursor()

# Create the messages table if it doesn't exist
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        channel TEXT,
        timestamp TEXT,
        message TEXT
    )
''')
db_conn.commit()

# ----------------------------
# Discord Bot Integration
# ----------------------------

class MyDiscordClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
    
    async def on_message(self, message):
        # Ignore messages sent by the bot itself
        if message.author == self.user:
            return

        # Gather message details
        user = str(message.author)
        channel = str(message.channel)
        timestamp = message.created_at.isoformat()
        content = message.content
        
        # Get the avatar URL with error handling
        try:
            if hasattr(message.author, 'avatar') and message.author.avatar:
                avatar_url = message.author.avatar.url
            else:
                avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"  # Default avatar
        except Exception as e:
            print(f"Error getting avatar: {e}")
            avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"  # Default avatar
        
        # Log message details to the SQLite database
        db_cursor.execute(
            "INSERT INTO messages (user, channel, timestamp, message) VALUES (?, ?, ?, ?)",
            (user, channel, timestamp, content)
        )
        db_conn.commit()
        
        # For debugging/logging:
        print(f"Logged message from {user} in {channel} at {timestamp}")
        
        # Emit the new message event to connected SocketIO clients
        message_data = {
            "user": user,
            "channel": channel,
            "timestamp": timestamp,
            "message": content,
            "avatar": avatar_url
        }
        socketio.emit('new_message', message_data)

# Create intents object and enable message content
intents = discord.Intents.default()
intents.message_content = True

# Create a Discord client instance with intents
discord_client = MyDiscordClient(intents=intents)

# The function to run the Discord bot in a separate thread
def run_discord_bot():
    DISCORD_BOT_TOKEN = " "  # Insert your Discord bot token here
    discord_client.run(maricon.bottoken)

# ----------------------------
# Main Entrypoint
# ----------------------------
if __name__ == '__main__':
    # Start the background thread that continuously updates and emits our metrics
    thread = threading.Thread(target=update_metrics)
    thread.daemon = True
    thread.start()
    
    # Start a background thread for the Discord bot
    discord_thread = threading.Thread(target=run_discord_bot)
    discord_thread.daemon = True
    discord_thread.start()
    
    # Run the Flask app with SocketIO support
    socketio.run(app, host='0.0.0.0', port=5090) 