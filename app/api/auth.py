import secrets
import sqlite3

from fastapi import HTTPException

from app.settings import config
from app.utils.hashing import hash_password, verify_password


class AuthManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def login(self, username, password):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result is None or not verify_password(password, result[0]):
            conn.close()
            raise ValueError("Неверный логин или пароль")

        session_token = secrets.token_urlsafe(16)
        cursor.execute(
            "INSERT OR REPLACE INTO sessions (username, session_token) VALUES (?, ?)",
            (username, session_token),
        )
        conn.commit()
        conn.close()
        return session_token

    def register(self, username, password, security_key):
        if security_key != config.SECURITY_KEY:
            raise ValueError("Неверный секрет")

        hashed = hash_password(password)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Пользователь уже существует")
        finally:
            conn.close()

    def logout(self, username):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM sessions WHERE username = ?", (username,))
        conn.commit()
        conn.close()

    def delete(self, username):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        cursor.execute("DELETE FROM keys WHERE username = ?", (username,))
        conn.commit()
        conn.close()

    def get_current_user(self, request):
        user = request.session.get("user")
        token = request.session.get("token")
        if not user or not token:
            raise HTTPException(status_code=401)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT session_token FROM sessions WHERE username = ?", (user,))
        result = cursor.fetchone()
        conn.close()

        if result is None or result[0] != token:
            raise HTTPException(status_code=401)
        return user

    def check_session(self, request):
        user = request.session.get("user")
        token = request.session.get("token")
        if not user or not token:
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT session_token FROM sessions WHERE username = ?", (user,))
        result = cursor.fetchone()
        conn.close()

        if result is None or result[0] != token:
            return None
        return user

    def submit_uid(self, username, uid):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM keys WHERE username = ?", (username,))
            cursor.execute(
                "INSERT INTO keys (username, uid) VALUES (?, ?)", (username, uid)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Такой UID уже записан.")
        finally:
            conn.close()


auth = AuthManager(config.DATABASE)
