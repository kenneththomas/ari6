from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from datetime import datetime
import json

app = Flask(__name__)

def get_db_connection(db_name='gato.db'):
    """Create a database connection"""
    db_path = os.path.join('logs', db_name)
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_available_databases():
    """Get list of available database files in logs directory"""
    db_files = []
    logs_dir = 'logs'
    if os.path.exists(logs_dir):
        for file in os.listdir(logs_dir):
            if file.endswith('.db'):
                db_files.append(file)
    return db_files

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
        databases = request.args.get('databases', 'gato.db').split(',')
        
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
        
        # Execute query across all selected databases
        all_logs = []
        total_count = 0
        
        for db_name in databases:
            conn = get_db_connection(db_name.strip())
            if conn is None:
                continue
                
            cursor = conn.cursor()
            
            try:
                # First, get the total count of matching results for this database
                count_sql = sql.replace("SELECT sender, channel, timestamp, message", "SELECT COUNT(*)")
                count_sql = count_sql.replace(" ORDER BY timestamp DESC LIMIT ? OFFSET ?", "")
                cursor.execute(count_sql, params[:-2])  # Remove limit and offset from params
                db_count = cursor.fetchone()[0]
                total_count += db_count
                
                # Now execute the main query WITHOUT pagination for this database
                # We need all results to sort them properly across databases
                query_sql = sql.replace(" ORDER BY timestamp DESC LIMIT ? OFFSET ?", " ORDER BY timestamp DESC")
                cursor.execute(query_sql, params[:-2])  # Remove limit and offset from params
                results = cursor.fetchall()
                
                # Convert to list of dictionaries and add database source
                for row in results:
                    all_logs.append({
                        'sender': row['sender'],
                        'channel': row['channel'],
                        'timestamp': row['timestamp'],
                        'message': row['message'],
                        'database': db_name
                    })
                    
            except Exception as e:
                print(f"Error querying {db_name}: {e}")
            finally:
                conn.close()
        
        # Sort all results by timestamp (newest first)
        all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply pagination to combined results
        start_idx = offset
        end_idx = start_idx + limit
        paginated_logs = all_logs[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'logs': paginated_logs,
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
        databases = request.args.get('databases', 'gato.db').split(',')
        
        total_messages = 0
        all_senders = set()
        all_channels = set()
        all_top_senders = {}
        all_top_channels = {}
        
        for db_name in databases:
            conn = get_db_connection(db_name.strip())
            if conn is None:
                continue
                
            cursor = conn.cursor()
            
            try:
                # Get total message count for this database
                cursor.execute("SELECT COUNT(*) as count FROM logs")
                db_messages = cursor.fetchone()['count']
                total_messages += db_messages
                
                # Get unique senders for this database
                cursor.execute("SELECT DISTINCT sender FROM logs")
                db_senders = [row['sender'] for row in cursor.fetchall()]
                all_senders.update(db_senders)
                
                # Get unique channels for this database
                cursor.execute("SELECT DISTINCT channel FROM logs")
                db_channels = [row['channel'] for row in cursor.fetchall()]
                all_channels.update(db_channels)
                
                # Get top senders for this database
                cursor.execute("""
                    SELECT sender, COUNT(*) as count 
                    FROM logs 
                    GROUP BY sender 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                db_top_senders = cursor.fetchall()
                for row in db_top_senders:
                    sender = row['sender']
                    count = row['count']
                    if sender in all_top_senders:
                        all_top_senders[sender] += count
                    else:
                        all_top_senders[sender] = count
                
                # Get top channels for this database
                cursor.execute("""
                    SELECT channel, COUNT(*) as count 
                    FROM logs 
                    GROUP BY channel 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                db_top_channels = cursor.fetchall()
                for row in db_top_channels:
                    channel = row['channel']
                    count = row['count']
                    if channel in all_top_channels:
                        all_top_channels[channel] += count
                    else:
                        all_top_channels[channel] = count
                        
            except Exception as e:
                print(f"Error getting stats from {db_name}: {e}")
            finally:
                conn.close()
        
        # Convert aggregated data to lists
        top_senders = [{'sender': sender, 'count': count} for sender, count in 
                      sorted(all_top_senders.items(), key=lambda x: x[1], reverse=True)[:10]]
        top_channels = [{'channel': channel, 'count': count} for channel, count in 
                       sorted(all_top_channels.items(), key=lambda x: x[1], reverse=True)[:10]]
        
        return jsonify({
            'success': True,
            'stats': {
                'total_messages': total_messages,
                'unique_senders': len(all_senders),
                'unique_channels': len(all_channels),
                'top_senders': top_senders,
                'top_channels': top_channels
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/databases')
def get_databases():
    """Get list of available databases"""
    try:
        databases = get_available_databases()
        return jsonify({
            'success': True,
            'databases': databases
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 