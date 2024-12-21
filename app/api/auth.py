from app.utils.hashing import *
from app import app, config

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

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
    # Метод получения ключа описан в роуте на страницу, там он и генерируется и отправляется в консоль
    if security_key != config.SECURITY_KEY:
        raise ValueError("Неверный секрет")
    # Если ключ верный, то происходит хеширование пароля и попытка помещения его в датабазу, данные вставляются в столбцы username и password
    # id генерируется автоматически для каждого нового пользователя в первом столбце датабазы
    elif security_key == config.SECURITY_KEY:
        hashed_password = hash_password(password)
        conn = sqlite3.connect(config.DATABASE)
        cursor = conn.cursor()
        # Если столбец с подобным значением username уже существует то в sqlite3 будет вызвана ошибка целостности и можно сказать что пользователь уже существует
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
    # Из таблицы sessions удаляется строка, где столбец username равен переданному в функцию
    cursor.execute("DELETE FROM sessions WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return True

# Функция для удаления аккаунта из датабазы
def delete_user(username: str):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    # Из датабазы удаляется строки из таблиц users и proxmark, где столбец username равен переданному в функцию
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    cursor.execute("DELETE FROM proxmark WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return True

def get_current_user(request: Request):
    # Получаем текущего юзера и токен из сессионнного куки
    user = request.session.get('user')
    token = request.session.get('token')
    # Если в сессионном куки отсутсвует юзер или токен, то возвращаем ошибку 401
    if not user or not token:
        raise HTTPException(status_code=401)
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    # В таблице sessions получаем значение из столбца session_token, в той строке где столбец username равен полученному из куки токена
    cursor.execute("SELECT session_token FROM sessions WHERE username = ?", (user,))
    result = cursor.fetchone()
    conn.close()

    # Если токен не совпадает или запись не найдена, то возвращаем ошибку 401
    if result is None or result[0] != token:
        raise HTTPException(status_code=401)
    # Возвращаем имя пользователя, если сессия валидна
    return user

# Эндпоинт с JSON форматом для проверки текущего пользователя и статуса аутентификации
@app.get("/session_status", response_class=JSONResponse)
async def session_status(request: Request):
    # Получение текущего пользователя и токена из куки
    user = request.session.get('user')
    token = request.session.get('token')

    # Если нет юзернейма или токена то возвращаем то, что пользователь не авторизован
    if not user or not token:
        return {"authenticated": False}

    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    # В таблице sessions получаем значение из столбца session_token, в той строке где столбец username равен полученному из куки токена
    cursor.execute("SELECT session_token FROM sessions WHERE username = ?", (user,))
    result = cursor.fetchone()
    conn.close()

    # Если в датабазе ничего не было найдено или если сессионный токен не равен полученному из датабазы то возвращаем то, что пользователь не авторизован
    if result is None or result[0] != token:
        return {"authenticated": False}

    # Во всех других случаях сессия валидна, тогда возвращаем текущего юзера и подтверждаем то, что он авторизован
    return {"authenticated": True, "username": user}
