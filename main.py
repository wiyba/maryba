import subprocess
import time
import os
import cv2
import sqlite3
import secrets
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse, RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="mysecretkey")
templates = Jinja2Templates(directory="templates")

VIDEO_PATH = os.path.join("templates/assets/videos", "video.mp4")
PHOTO_PATH = os.path.join("templates/assets/photos", "image.jpg")
DATABASE = "users.db"

# ONVIF setup
ip = '192.168.207.71'
username = 'admin'
password = 'rubetek11'
rtsp_url = f"rtsp://{username}:{password}@{ip}:8554/Streaming/Channels/101"

ffmpeg_process = None

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn.commit()
    conn.close()

init_db()

# Проверка авторизации
def get_current_user(request: Request):
    user = request.session.get('user')
    token = request.session.get('token')
    if not user or not token:
        raise HTTPException(status_code=401, detail="Необходима авторизация")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT session_token FROM sessions WHERE username = ?", (user,))
    result = cursor.fetchone()
    conn.close()

    if result is None or result[0] != token:
        raise HTTPException(status_code=401, detail="Сессия недействительна")

    return user

# Авторизация
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    if user is None:
        conn.close()
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    session_token = secrets.token_urlsafe(16)
    cursor.execute("INSERT OR REPLACE INTO sessions (username, session_token) VALUES (?, ?)", (username, session_token))
    conn.commit()
    conn.close()

    request.session['user'] = username
    request.session['token'] = session_token
    return RedirectResponse("/", status_code=302)

@app.get("/logout")
async def logout(request: Request):
    user = request.session.get('user')
    if user:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE username = ?", (user,))
        conn.commit()
        conn.close()

    request.session.clear()
    return RedirectResponse("/")

# Регистрация пользователя
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    conn.close()
    return RedirectResponse("/login", status_code=302)




# Функции для работы с ffmpeg

def start_ffmpeg():
    global ffmpeg_process, audio_process
    if ffmpeg_process is None or ffmpeg_process.poll() is not None:
        ffmpeg_process = subprocess.Popen([
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-fflags', 'nobuffer',
            '-flags', 'low_delay',
            '-analyzeduration', '1000000',
            '-probesize', '1000000',
            '-fflags', '+discardcorrupt',
            '-i', rtsp_url,
            '-f', 'mpegts',
            '-codec:v', 'mpeg1video',
            '-q', '5',
            'udp://127.0.0.1:1234'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)




def stop_ffmpeg():
    global ffmpeg_process
    if isinstance(ffmpeg_process, subprocess.Popen):
        try:
            print("Попытка завершить процесс...")
            ffmpeg_process.terminate()
            ffmpeg_process.wait(timeout=5)
        except Exception as e:
            print(f"Ошибка при завершении процесса: {e}. Пробуем kill()")
            ffmpeg_process.kill()
        finally:
            ffmpeg_process = None
    else:
        print("Процесс ffmpeg не был запущен или уже завершен.")


async def video_stream(request: Request):
    start_ffmpeg()
    cap = cv2.VideoCapture("udp://127.0.0.1:1234")

    try:
        while True:
            if await request.is_disconnected():
                print("Клиент отключился, останавливаем поток")
                break

            ret, frame = cap.read()
            if not ret:
                print("Не удалось получить кадр")
                break

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    except Exception as e:
        print(f"Ошибка при обработке потока: {e}")

    finally:
        cap.release()
        stop_ffmpeg()
        print("Поток завершен")




# 1. Статические страницы
@app.get("/")
async def root():
    return FileResponse("templates/main.html")

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# 2. Статические медиа-файлы
@app.get("/video")
def video():
    return FileResponse(VIDEO_PATH, media_type="video/mp4")

# 3. API-запросы и проверка статуса сессии
@app.get("/session_status", response_class=JSONResponse)
async def session_status(request: Request):
    user = request.session.get('user')
    token = request.session.get('token')
    if not user or not token:
        return {"authenticated": False}

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT session_token FROM sessions WHERE username = ?", (user,))
    result = cursor.fetchone()
    conn.close()

    if result is None or result[0] != token:
        return {"authenticated": False}

    return {"authenticated": True}

# ONVIF ссылки
@app.get("/onvif")
async def onvif(request: Request):
    get_current_user(request)
    with open("templates/onvif.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

@app.get("/onvif_source")
async def onvif_source(request: Request):
    get_current_user(request)
    return StreamingResponse(video_stream(request), media_type="multipart/x-mixed-replace; boundary=frame")