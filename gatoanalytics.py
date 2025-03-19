from flask import Flask
from flask_socketio import SocketIO
import threading
import time
import random

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
    In your real implementation, you could have the Discord bot update these metrics
    via a shared data store/API or integrate direct event handling.
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
    Serves a simple HTML dashboard page.
    The client-side JavaScript establishes a websocket connection back to the server
    and updates the page live with analytics data.
    """
    return '''
    <!DOCTYPE html>
    <html>
      <head>
        <title>Realtime Discord Analytics Dashboard</title>
      </head>
      <body>
        <h1>Discord Server Analytics Dashboard</h1>
        <div>
          <p>Total Messages: <span id="total_messages">0</span></p>
          <p>Total Reactions: <span id="total_reactions">0</span></p>
          <p>Active Users: <span id="active_users">0</span></p>
        </div>
        <!-- Load SocketIO client library from a CDN -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.0/socket.io.min.js"></script>
        <script type="text/javascript">
          var socket = io();
          // Listen for the metrics_update event and update the HTML content accordingly
          socket.on('metrics_update', function(data) {
              document.getElementById('total_messages').innerText = data.total_messages;
              document.getElementById('total_reactions').innerText = data.total_reactions;
              document.getElementById('active_users').innerText = data.active_users;
          });
        </script>
      </body>
    </html>
    '''

if __name__ == '__main__':
    # Start the background thread that continuously updates and emits our metrics
    thread = threading.Thread(target=update_metrics)
    thread.daemon = True
    thread.start()
    
    # Run the Flask app with SocketIO support
    socketio.run(app, host='0.0.0.0', port=5090) 