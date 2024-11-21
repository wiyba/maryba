from app.config import config
import sqlite3


def init_db():
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        username TEXT PRIMARY KEY,
        session_token TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cameras (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        ip TEXT NOT NULL,
        login TEXT NOT NULL,
        password TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users(username)
    )
    """)

    conn.commit()
    conn.close()