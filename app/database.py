import sqlite3

from app.settings import config


def init_db():
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()

    # схемы
    # пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # веб сессий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            username TEXT UNIQUE PRIMARY KEY,
            session_token TEXT NOT NULL
        )
    """)

    # камер
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY,
            location TEXT NOT NULL
        )
    """)

    # считывателей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS readers (
            id INTEGER PRIMARY KEY,
            location TEXT NOT NULL
        )
    """)

    # идентификаторов пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            uid TEXT UNIQUE NOT NULL,
            counter INTEGER DEFAULT 0,
            warnings INTEGER DEFAULT 0,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    """)

    # журнала событий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            uid TEXT,
            username TEXT,
            event_type TEXT NOT NULL,
            balance INTEGER,
            video_path TEXT,
            is_suspicious INTEGER DEFAULT 0,
            anomaly_reason TEXT
        )
    """)

    # журнала аномалий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            reason TEXT,
            resolved INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
