from datetime import datetime, timedelta
import mememgr
import os
import sqlite3

# Configuration for batching
BATCH_SIZE = 25  # Number of messages to accumulate before writing to the database
FLUSH_INTERVAL = timedelta(minutes=5)  # Time to wait before flushing to the database

# Initialize
dbfilename = os.environ.get("ARI_LOG_DB", "logs/gato.db")
batch_buffer = []
last_write_time = datetime.now()
xp_buffer = {}
previous_xp_buffer = {}

MESSAGE_IDENTITY_COLUMNS = {
    "message_id": "TEXT",
    "author_id": "TEXT",
    "author_display_name": "TEXT",
    "author_is_bot": "INTEGER",
    "channel_id": "TEXT",
    "guild_id": "TEXT",
    "thread_id": "TEXT",
    "reply_to_message_id": "TEXT",
    "attachment_count": "INTEGER",
    "embed_count": "INTEGER",
}

# Ensure the selected database directory exists.
os.makedirs(os.path.dirname(dbfilename) or ".", exist_ok=True)

def _ensure_xp_table(conn):
    """xp rows must be unique per user; INSERT OR REPLACE only works with a PK/UNIQUE on user."""
    cur = conn.cursor()
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='xp'")
    row = cur.fetchone()
    if row is None:
        cur.execute(
            "CREATE TABLE xp (user TEXT PRIMARY KEY NOT NULL, xp INTEGER NOT NULL)"
        )
        return
    ddl = (row[0] or "").upper()
    if "PRIMARY KEY" in ddl:
        return
    cur.execute(
        "CREATE TABLE xp_new (user TEXT PRIMARY KEY NOT NULL, xp INTEGER NOT NULL)"
    )
    cur.execute(
        "INSERT INTO xp_new SELECT user, MAX(xp) FROM xp GROUP BY user"
    )
    cur.execute("DROP TABLE xp")
    cur.execute("ALTER TABLE xp_new RENAME TO xp")


def _ensure_schema(conn):
    """Create current tables and add new columns to legacy databases in place."""
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS logs (
            sender TEXT,
            channel TEXT,
            timestamp TEXT,
            date TEXT,
            hour TEXT,
            message TEXT
        )"""
    )
    existing_columns = {
        row[1] for row in cur.execute("PRAGMA table_info(logs)").fetchall()
    }
    for column, column_type in MESSAGE_IDENTITY_COLUMNS.items():
        if column not in existing_columns:
            cur.execute(f"ALTER TABLE logs ADD COLUMN {column} {column_type}")

    cur.execute(
        """CREATE TABLE IF NOT EXISTS reaction_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            message_id TEXT,
            channel_id TEXT,
            guild_id TEXT,
            reactor_id TEXT,
            reactor_name TEXT,
            reactor_display_name TEXT,
            reactor_is_bot INTEGER,
            emoji TEXT NOT NULL,
            emoji_id TEXT,
            emoji_name TEXT,
            timestamp TEXT NOT NULL
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS ai_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            purpose TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            latency_ms REAL NOT NULL,
            attempt_count INTEGER NOT NULL,
            success INTEGER NOT NULL,
            status_code INTEGER,
            error_type TEXT,
            cost REAL
        )"""
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_message_id ON logs(message_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_author_id ON logs(author_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_channel_id ON logs(channel_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_reactions_message_id "
        "ON reaction_events(message_id)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_reactions_reactor_id "
        "ON reaction_events(reactor_id)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_reactions_timestamp "
        "ON reaction_events(timestamp)"
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_calls_timestamp ON ai_calls(timestamp)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_calls_model ON ai_calls(model)")
    _ensure_xp_table(conn)


def _connect():
    return sqlite3.connect(dbfilename)


# Ensure the database and tables exist, then populate the XP cache.
conn = _connect()
_ensure_schema(conn)
c = conn.cursor()

c.execute("SELECT * FROM xp")
result = c.fetchall()
for row in result:
    xp_buffer[row[0]] = row[1]
# we use previous xp buffer to track changes to xp_buffer
previous_xp_buffer = xp_buffer.copy()
conn.commit()
conn.close()

def flush_to_db():
    print('Flushing to database')
    global batch_buffer, last_write_time, xp_buffer
    if not batch_buffer:
        return

    conn = _connect()
    c = conn.cursor()
    c.executemany(
        """INSERT INTO logs (
            sender, channel, timestamp, date, hour, message,
            message_id, author_id, author_display_name, author_is_bot,
            channel_id, guild_id, thread_id, reply_to_message_id,
            attachment_count, embed_count
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        batch_buffer,
    )
    #print(f'xp updates: {xp_buffer}')

    # Update all changed XP values in one batch
    xp_updates = []
    for user, xp in xp_buffer.items():
        if user not in previous_xp_buffer or xp != previous_xp_buffer[user]:
            print(f'XP change for {user}: {previous_xp_buffer.get(user, 0)} -> {xp}')
            xp_updates.append((user, xp))
    
    if xp_updates:
        c.executemany("INSERT OR REPLACE INTO xp VALUES (?,?)", xp_updates)
        # Update previous_xp_buffer after all changes are committed
        previous_xp_buffer.update({user: xp for user, xp in xp_updates})
    
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

    author = msg.author
    message_id = str(msg.id) if getattr(msg, "id", None) is not None else None
    author_id = str(author.id) if getattr(author, "id", None) is not None else None
    author_display_name = str(
        getattr(author, "display_name", getattr(author, "name", sender))
    )
    author_is_bot = int(bool(getattr(author, "bot", False)))
    channel_id = (
        str(msg.channel.id) if getattr(msg.channel, "id", None) is not None else None
    )
    guild = getattr(msg, "guild", None)
    guild_id = str(guild.id) if getattr(guild, "id", None) is not None else None
    thread_id = channel_id if getattr(msg.channel, "parent_id", None) is not None else None
    reference = getattr(msg, "reference", None)
    reply_id = getattr(reference, "message_id", None)
    reply_to_message_id = str(reply_id) if reply_id is not None else None
    attachment_count = len(getattr(msg, "attachments", ()) or ())
    embed_count = len(getattr(msg, "embeds", ()) or ())

    newlog = f'[{timestamp}] ({channel}) {sender}: {message}'
    print(newlog)
    
    # no further processing on bot commands
    if message.startswith('!') or message.startswith('t!'):
        return
    
    # ignore config channel
    if channel == 'config':
        return

    # Add to batch buffer
    batch_buffer.append(
        (
            sender,
            channel,
            timestamp,
            date,
            hour,
            message,
            message_id,
            author_id,
            author_display_name,
            author_is_bot,
            channel_id,
            guild_id,
            thread_id,
            reply_to_message_id,
            attachment_count,
            embed_count,
        )
    )

    # if sender not in xp_buffer, see if they are in the xp table and add to buffer
    if sender not in xp_buffer:
        print(f'Checking for XP for {sender}')
        conn = _connect()
        c = conn.cursor()
        c.execute("SELECT xp FROM xp WHERE user = ?", (sender,))
        result = c.fetchone()
        if result:
            xp_buffer[sender] = result[0]
        else:
            print(f'No XP found for {sender}, adding to buffer')
            xp_buffer[sender] = 0
        conn.close()

    add_xp_user(sender, 1)
    
    # Check if it's time to flush the buffer
    if len(batch_buffer) >= BATCH_SIZE or (now - last_write_time) >= FLUSH_INTERVAL:
        print(f'batch_buffer length: {len(batch_buffer)}, time since last write: {now - last_write_time}')
        flush_to_db()


def log_reaction_event(payload, action):
    """Persist a raw reaction event, including events for uncached messages."""
    if action not in {"add", "remove"}:
        raise ValueError("reaction action must be 'add' or 'remove'")

    member = getattr(payload, "member", None)
    emoji = payload.emoji
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO reaction_events (
                action, message_id, channel_id, guild_id, reactor_id,
                reactor_name, reactor_display_name, reactor_is_bot,
                emoji, emoji_id, emoji_name, timestamp
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                action,
                str(payload.message_id),
                str(payload.channel_id),
                str(payload.guild_id) if payload.guild_id is not None else None,
                str(payload.user_id),
                str(member.name) if getattr(member, "name", None) is not None else None,
                (
                    str(member.display_name)
                    if getattr(member, "display_name", None) is not None
                    else None
                ),
                int(bool(member.bot)) if member is not None else None,
                str(emoji),
                str(emoji.id) if getattr(emoji, "id", None) is not None else None,
                str(emoji.name) if getattr(emoji, "name", None) is not None else None,
                str(datetime.now()),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def log_ai_call(
    *,
    provider,
    model,
    purpose,
    input_tokens,
    output_tokens,
    total_tokens,
    latency_ms,
    attempt_count,
    success,
    status_code=None,
    error_type=None,
    cost=None,
):
    """Persist AI operational metadata. Prompts and outputs are never accepted."""
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO ai_calls (
                timestamp, provider, model, purpose, input_tokens,
                output_tokens, total_tokens, latency_ms, attempt_count,
                success, status_code, error_type, cost
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(datetime.now()),
                provider,
                model,
                purpose,
                input_tokens,
                output_tokens,
                total_tokens,
                latency_ms,
                attempt_count,
                int(bool(success)),
                status_code,
                error_type,
                cost,
            ),
        )
        conn.commit()
    finally:
        conn.close()

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
    
def get_top_10_xp_users():
    top_10 = sorted(xp_buffer.items(), key=lambda item: item[1], reverse=True)[:10]
    max_user_len = max(len(user) for user, xp in top_10)
    max_xp_len = max(len(str(xp)) for user, xp in top_10)
    
    top_10_str = "\n".join([f"`{i+1:2}. {user:<{max_user_len}} : {xp:>{max_xp_len}}`" 
                            for i, (user, xp) in enumerate(top_10)])
    return f"**Top 10 XP Users:**\n{top_10_str}"
