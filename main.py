import os
os.system("pip freeze > requirements.txt")
import subprocess
import time
import cv2
import sqlite3
import secrets
import threading
import asyncio
import bcrypt
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse, RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware( # type: ignore
    SessionMiddleware,
    secret_key=os.urandom(64),
    session_cookie="my_session",
    https_only=True,
    same_site="strict"
)
templates = Jinja2Templates(directory="templates")

VIDEO_PATH = os.path.join("static/images/videos", "video.mp4")
PHOTO_PATH = os.path.join("templates/assets/photos", "image.jpg")
DATABASE = "users.db"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# Настройка ONVIF
ip = '192.168.207.71'
user = 'admin'
passwd = 'rubetek11'
rtsp_url = f"rtsp://{user}:{passwd}@{ip}:8554/Streaming/Channels/101"

ffmpeg_process = None
streaming_active = False
camera_check_task = None

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Создаем таблицу пользователей с автоинкрементом ID без использования AUTOINCREMENT
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Создаем таблицу сессий
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        username TEXT PRIMARY KEY,
        session_token TEXT NOT NULL
    )
    """)

    # Создаем таблицу камер с полями для IP, логина и пароля
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cameras (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        ip TEXT NOT NULL,
        login TEXT NOT NULL,
        password TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users(username)
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
    # Извлекаем хешированный пароль из базы данных
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    if result is None:
        conn.close()
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    hashed_password = result[0]
    # Проверяем введенный пароль с хешированным паролем из базы данных
    if not verify_password(password, hashed_password):
        conn.close()
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    # Если проверка успешна, создаем сессионный токен
    session_token = secrets.token_urlsafe(16)
    cursor.execute("INSERT OR REPLACE INTO sessions (username, session_token) VALUES (?, ?)", (username, session_token))
    conn.commit()
    conn.close()

    request.session['user'] = username
    request.session['token'] = session_token
    return RedirectResponse("/", status_code=302)


# Деавторизация
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
    hashed_password = hash_password(password)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    try:
        # Сохраняем пользователя с хешированным паролем
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    conn.close()

    return RedirectResponse("/login", status_code=302)


# Проверка доступности камеры
def check_camera_availability():
    try:
        print("Проверка доступности камеры с помощью ffmpeg...")
        result = subprocess.run(
            [
                'ffmpeg',
                '-rtsp_transport', 'tcp',
                '-i', rtsp_url,
                '-t', '3',  # Проверка камеры в течение 3 секунд
                '-f', 'null', '-'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5  # Таймаут в 5 секунд
        )
        if result.returncode != 0:
            print("Камера недоступна. Остановка потока.")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("Проверка камеры завершилась по таймауту. Камера недоступна.")
        return False





# Функция для запуска ffmpeg
async def start_ffmpeg():
    global ffmpeg_process, streaming_active
    print("Проверка доступности камеры...")

    # Используем проверку доступности через ffmpeg
    if not check_camera_availability():
        stop_ffmpeg()
        return

    if ffmpeg_process is None or ffmpeg_process.poll() is not None:
        print("Запуск ffmpeg...")
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
        streaming_active = True




# Функция для остановки ffmpeg
def stop_ffmpeg():
    global ffmpeg_process, streaming_active
    if isinstance(ffmpeg_process, subprocess.Popen):
        try:
            print("Остановка ffmpeg...")
            ffmpeg_process.terminate()
            ffmpeg_process.wait(timeout=5)
        except Exception as e:
            print(f"Ошибка при завершении ffmpeg: {e}. Пробуем kill()")
            ffmpeg_process.kill()
        finally:
            ffmpeg_process = None
            streaming_active = False
    else:
        print("Процесс ffmpeg не был запущен.")



# Функция ffmpeg
async def video_stream(request: Request):
    global streaming_active

    if not streaming_active:
        await start_ffmpeg()

    if not streaming_active:
        print("Поток не запущен, камера недоступна.")
        return

    cap = cv2.VideoCapture("udp://127.0.0.1:1234")

    if not cap.isOpened():
        print("Не удалось открыть поток видео. Остановка потока.")
        stop_ffmpeg()
        return

    try:
        while True:
            if await request.is_disconnected():
                print("Пользователь покинул страницу, останавливаем поток.")
                break

            ret, frame = cap.read()
            if not ret:
                print("Не удалось получить кадр. Остановка потока.")
                break

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    except Exception as e:
        print(f"Ошибка при обработке видео потока: {e}")

    finally:
        cap.release()
        stop_ffmpeg()
        print("Видео поток завершён.")



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
async def video(request: Request):
    get_current_user(request)
    return FileResponse(VIDEO_PATH, media_type="video/mp4")

# 3. API-запросы и проверка статуса сессии
# Обновленная проверка сессии
@app.get("/session_status", response_class=JSONResponse)
async def session_status(request: Request):
    user = request.session.get('user')
    token = request.session.get('token')

    # Проверка наличия данных в сессии
    if not user or not token:
        return {"authenticated": False}

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT session_token FROM sessions WHERE username = ?", (user,))
    result = cursor.fetchone()
    conn.close()

    # Сравниваем токен с сессией
    if result is None or result[0] != token:
        return {"authenticated": False}

    # Если сессия валидна, отправляем успешный статус
    return {"authenticated": True, "username": user}


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