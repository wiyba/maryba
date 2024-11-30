from app.config import config
from app.utils.hashing import hash_password, verify_password
import sqlite3
import secrets


def login_user(username: str, password: str):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    if result is None:
        conn.close()
        raise ValueError("Неверный логин или пароль")

    hashed_password = result[0]

    if not verify_password(password, hashed_password):
        conn.close()
        raise ValueError("Неверный логин или пароль")

    session_token = secrets.token_urlsafe(16)
    cursor.execute("INSERT OR REPLACE INTO sessions (username, session_token) VALUES (?, ?)", (username, session_token))
    conn.commit()
    conn.close()

    return session_token


def register_user(username: str, password: str, security_key: str):
    if security_key != config.SECURITY_KEY:
        raise ValueError("Неверный секрет")
    elif security_key == config.SECURITY_KEY:
        hashed_password = hash_password(password)
        conn = sqlite3.connect(config.DATABASE)
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError("Пользователь уже существует")
        conn.close()
    else:
        raise ValueError("Неизвестная ошибка")


def logout_user(username: str):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return True


def delete_user(username: str):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    cursor.execute("DELETE FROM proxmark WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return True
