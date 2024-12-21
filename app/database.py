from app import config

import sqlite3

# Функция для создания (инициации) датабазы
def init_db():
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Таблица сессий
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        username TEXT UNIQUE PRIMARY KEY,
        session_token TEXT NOT NULL
    )
    """)

    # Таблица proxmark
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proxmark (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        uid TEXT UNIQUE NOT NULL,
        counter INTEGER DEFAULT 0,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    """)

    conn.commit()
    conn.close()