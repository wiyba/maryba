from app.utils.hashing import hash_password, verify_password
from app.config import config
import sqlite3
import secrets

# Функция для входа в аккаунт и создания нового сессионного куки в датабазе
def login_user(username: str, password: str):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()

    # Получение хеша пароля столбца passwords из таблицы users с столбцом username равным юзернейму из формы
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    # Если такой строки нет то возвращает:
    if result is None:
        conn.close()
        raise ValueError("Неверный логин или пароль")

    # Преобразование полученного из бд пароля в переменную
    hashed_password = result[0]

    # Функция verify_password сверяет хеш с введенным значением и если они не совпадают то возвращает:
    if not verify_password(password, hashed_password):
        conn.close()
        raise ValueError("Неверный логин или пароль")

    # Если все хорошо, то генерирует куки файл с хешом сессии и вставляет его в таблицу с активными сессиями (sessions), где есть столбец с юзернеймом и токеном сессии
    session_token = secrets.token_urlsafe(16)
    cursor.execute("INSERT OR REPLACE INTO sessions (username, session_token) VALUES (?, ?)", (username, session_token))
    conn.commit()
    conn.close()

    return session_token

# Функция для регистрации нового пользователя
# Также проверяется чтобы SECURITY_KEY который генерируется при входе на /register был верный
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

# Скрипт для удаления сессионного куки и выхода из аккаунта
def logout_user(username: str):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return True

# Функция для удаления аккаунта из датабазы
def delete_user(username: str):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    cursor.execute("DELETE FROM proxmark WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return True
