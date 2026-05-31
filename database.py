import sqlite3

DB_PATH = "chatbot.db"


def init_db():
    """Create the messages table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT    NOT NULL,
            user_msg  TEXT    NOT NULL,
            bot_reply TEXT    NOT NULL,
            timestamp TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("Database initialized ✅")


def log_message(session_id: str, user_msg: str, bot_reply: str, timestamp: str):
    """Insert a conversation turn into the DB."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (session_id, user_msg, bot_reply, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, user_msg, bot_reply, timestamp),
    )
    conn.commit()
    conn.close()


def get_history(session_id: str) -> list[dict]:
    """Return all messages for a session as a list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_msg, bot_reply, timestamp FROM messages WHERE session_id = ? ORDER BY id",
        (session_id,),
    )
    rows = [
        {"user": row[0], "bot": row[1], "timestamp": row[2]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return rows
