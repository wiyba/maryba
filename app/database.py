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

    # Таблица камер
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cameras (
        id INTEGER PRIMARY KEY,
        location TEXT NOT NULL
    )
    """)

    # Таблица считывателей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS readers (
        id INTEGER PRIMARY KEY,
        location TEXT NOT NULL
    )
    """)

    # Таблица ключей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        uid TEXT UNIQUE NOT NULL,
        counter INTEGER DEFAULT 0,
        FOREIGN KEY (username) REFERENCES users (username)
    )
    """)

    conn.commit()
    conn.close()