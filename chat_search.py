from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime
import json

app = Flask(__name__)

def get_db_connection():
    """Create a database connection"""
    db_path = os.path.join('logs', 'gato.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Main search page"""
    return render_template('chat_search.html')

@app.route('/api/search')
def search_logs():
    """API endpoint for searching logs"""
    try:
        # Get search parameters
        query = request.args.get('query', '').strip()
        sender = request.args.get('sender', '').strip()
        channel = request.args.get('channel', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        # Build SQL query
        sql = "SELECT sender, channel, timestamp, message FROM logs WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (message LIKE ? OR sender LIKE ? OR channel LIKE ?)"
            search_term = f"%{query}%"
            params.extend([search_term, search_term, search_term])
        
        if sender:
            sql += " AND sender LIKE ?"
            params.append(f"%{sender}%")
        
        if channel:
            sql += " AND channel LIKE ?"
            params.append(f"%{channel}%")
        
        if date_from:
            sql += " AND date >= ?"
            params.append(date_from)
        
        if date_to:
            sql += " AND date <= ?"
            params.append(date_to)
        
        # Add ordering and pagination
        sql += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        # Execute query
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First, get the total count of matching results
        count_sql = sql.replace("SELECT sender, channel, timestamp, message", "SELECT COUNT(*)")
        count_sql = count_sql.replace(" ORDER BY timestamp DESC LIMIT ? OFFSET ?", "")
        cursor.execute(count_sql, params[:-2])  # Remove limit and offset from params
        total_count = cursor.fetchone()[0]
        
        # Now execute the main query with pagination
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        logs = []
        for row in results:
            logs.append({
                'sender': row['sender'],
                'channel': row['channel'],
                'timestamp': row['timestamp'],
                'message': row['message']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': total_count
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get statistics about the logs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total message count
        cursor.execute("SELECT COUNT(*) as count FROM logs")
        total_messages = cursor.fetchone()['count']
        
        # Get unique senders
        cursor.execute("SELECT COUNT(DISTINCT sender) as count FROM logs")
        unique_senders = cursor.fetchone()['count']
        
        # Get unique channels
        cursor.execute("SELECT COUNT(DISTINCT channel) as count FROM logs")
        unique_channels = cursor.fetchone()['count']
        
        # Get top senders
        cursor.execute("""
            SELECT sender, COUNT(*) as count 
            FROM logs 
            GROUP BY sender 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_senders = [dict(row) for row in cursor.fetchall()]
        
        # Get top channels
        cursor.execute("""
            SELECT channel, COUNT(*) as count 
            FROM logs 
            GROUP BY channel 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_channels = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_messages': total_messages,
                'unique_senders': unique_senders,
                'unique_channels': unique_channels,
                'top_senders': top_senders,
                'top_channels': top_channels
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 