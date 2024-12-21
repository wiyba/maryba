from app.config import config
from fastapi import Request
import sqlite3

# Скрипт для изменения UID, привязанного к пользователю в датабазе
def submit_uid(request: Request, uid: str):
    username = request.session.get('user')
    if not username:
        raise ValueError("Пользователь не авторизован")

    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM proxmark WHERE username = ?", (username,))
        cursor.execute("INSERT INTO proxmark (username, uid) VALUES (?, ?)", (username, uid))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("Произошла ошибка при записи UID")
    finally:
        conn.close()