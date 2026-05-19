import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "ramwise.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default',
            foreground_app TEXT NOT NULL,
            ram_usage INTEGER NOT NULL,
            cpu_usage INTEGER NOT NULL,
            battery_level INTEGER NOT NULL,
            timestamp INTEGER NOT NULL,
            received_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            predicted_apps TEXT NOT NULL,
            confidence_scores TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    try:
        cursor.execute("ALTER TABLE telemetry ADD COLUMN user_id TEXT NOT NULL DEFAULT 'default'")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    conn.close()
