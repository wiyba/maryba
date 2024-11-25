from app.main import app
from app.config import config
import sqlite3
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


def get_current_user(request: Request):
    user = request.session.get('user')
    token = request.session.get('token')
    if not user or not token:
        raise HTTPException(status_code=401)

    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT session_token FROM sessions WHERE username = ?", (user,))
    result = cursor.fetchone()
    conn.close()

    if result is None or result[0] != token:
        raise HTTPException(status_code=401, detail="Сессия недействительна")

    return user


@app.get("/session_status", response_class=JSONResponse)
async def session_status(request: Request):
    user = request.session.get('user')
    token = request.session.get('token')

    # Проверка наличия данных в сессии
    if not user or not token:
        return {"authenticated": False}

    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT session_token FROM sessions WHERE username = ?", (user,))
    result = cursor.fetchone()
    conn.close()

    # Сравниваем токен с сессией
    if result is None or result[0] != token:
        return {"authenticated": False}

    # Если сессия валидна, отправляем успешный статус
    return {"authenticated": True, "username": user}