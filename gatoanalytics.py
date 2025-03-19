from flask import Flask
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

# In-memory analytics data (replace these with real metrics from the discord bot as needed)
metrics = {
    'total_messages': 0,
    'total_reactions': 0,
    'active_users': 0
}

def update_metrics():
    """
    This background thread simulates updating analytics.
    In your real implementation, you might update these from real data.
    """
    while True:
        # Simulate increasing metrics with random increments
        metrics['total_messages'] += random.randint(0, 5)
        metrics['total_reactions'] += random.randint(0, 3)
        metrics['active_users'] = random.randint(5, 20)
        
        # Emit (push) the updated metrics to all connected clients
        socketio.emit('metrics_update', metrics)
        time.sleep(2)  # adjust interval as needed

@app.route('/')
def index():
    """
    Serves a realtime dashboard page with panels that can be dynamically
    added or removed. By default, there are two panels:
      - Metrics Panel (shows total messages/reactions/active users)
      - Latest Message Panel (shows the details of the most recent Discord message)
    """
    return '''
    <!DOCTYPE html>
    <html>
      <head>
        <title>Realtime Discord Analytics Dashboard</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
          }
          h1 {
            color: #5865F2;
            text-align: center;
          }
          .controls {
            text-align: center;
            margin-bottom: 20px;
          }
          button {
            background-color: #5865F2;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 4px;
            cursor: pointer;
          }
          button:hover {
            background-color: #4752C4;
          }
          #dashboard {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
          }
          .panel {
            border: 1px solid #ccc;
            padding: 15px;
            margin: 10px;
            border-radius: 8px;
            background-color: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            min-width: 300px;
            display: block; /* Ensure panels are visible by default */
          }
          .panel h2 {
            color: #5865F2;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            margin-top: 0;
          }
          #message_content {
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
          }
          .avatar-container {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
          }
          .avatar-container img {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            margin-right: 15px;
          }
          .message-details {
            margin-top: 10px;
          }
        </style>
      </head>
      <body>
        <h1>Discord Server Analytics Dashboard</h1>
        <div class="controls">
          <button onclick="addPanel('metrics_panel')">Show Metrics Panel</button>
          <button onclick="removePanel('metrics_panel')">Hide Metrics Panel</button>
          <button onclick="addPanel('latest_message_panel')">Show Latest Message Panel</button>
          <button onclick="removePanel('latest_message_panel')">Hide Latest Message Panel</button>
        </div>
        <div id="dashboard">
          <div id="metrics_panel" class="panel">
            <h2>Metrics</h2>
            <p>Total Messages: <span id="total_messages">0</span></p>
            <p>Total Reactions: <span id="total_reactions">0</span></p>
            <p>Active Users: <span id="active_users">0</span></p>
          </div>
          <div id="latest_message_panel" class="panel">
            <h2>Latest Message</h2>
            <div id="message_content">
              <p>Waiting for new messages...</p>
            </div>
          </div>
        </div>
        <!-- Load SocketIO client library from a CDN -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.0/socket.io.min.js"></script>
        <script type="text/javascript">
          var socket = io();
          
          // Listen for metrics updates and update the metrics panel
          socket.on('metrics_update', function(data) {
              document.getElementById('total_messages').innerText = data.total_messages;
              document.getElementById('total_reactions').innerText = data.total_reactions;
              document.getElementById('active_users').innerText = data.active_users;
          });
  
          // Listen for new messages and update the latest message panel
          socket.on('new_message', function(data) {
              let contentDiv = document.getElementById('message_content');
              contentDiv.innerHTML = `
                <div class="avatar-container">
                  <img src="${data.avatar}" alt="User Avatar">
                  <strong>${data.user}</strong>
                </div>
                <div class="message-details">
                  <p><strong>Channel:</strong> ${data.channel}</p>
                  <p><strong>Time:</strong> ${new Date(data.timestamp).toLocaleString()}</p>
                  <p><strong>Message:</strong> ${data.message}</p>
                </div>
              `;
          });
  
          // Functions to hide/show panels dynamically.
          function removePanel(panelId) {
              let panel = document.getElementById(panelId);
              if (panel) {
                  panel.style.display = 'none';
              }
          }
  
          function addPanel(panelId) {
              let panel = document.getElementById(panelId);
              if (panel) {
                  panel.style.display = 'block';
              }
          }
        </script>
      </body>
    </html>
    '''

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