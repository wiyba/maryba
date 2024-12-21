from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

import asyncio
import tkinter as tk
import os
import shutil

from app.config import config, proxmark
from app.utils.exceptions import render_error_page
from app.utils.charge import start_reader
from app.api.proxmark import proxmark_build
from app.utils.gui import set_root, task_queue

app = FastAPI()

# Подключение шаблонов и статических файлов
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR, html=True), name="static")
app.mount("/images", StaticFiles(directory=config.IMAGES_DIR, html=True), name="images")
app.mount("/videos", StaticFiles(directory=config.VIDEOS_DIR, html=True), name="videos")
app.mount("/js", StaticFiles(directory=config.JS_DIR, html=False), name="js")

# Настройка middleware для сессий
app.add_middleware(
    SessionMiddleware,
    secret_key=os.urandom(64),
    session_cookie="my_session",
    https_only=True,
    same_site="strict",
)


# Событие запуска приложения
@app.on_event("startup")
async def on_startup():
    from app.database import init_db
    init_db()
    from app.routes import main, auth, profile, onvif, gallery
    app.include_router(main.router)
    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(onvif.router)
    app.include_router(gallery.router)
    print("\nМодули успешно импортированы.")
    if proxmark.device_name != '' and os.path.exists(proxmark.client_path):
        asyncio.create_task(start_reader_task())
        asyncio.create_task(run_tkinter())
        print("Proxmark3 подключен")
    elif not os.path.exists(proxmark.client_path):
        print("Клиент Proxmark3 не найден")
        ans = int(input("Хотите ли забилдить сейчас? [0-1]: "))
        if ans == 1:
            asyncio.create_task(proxmark_build_task())
        else:
            print("Продалжаем без Proxmark3...")
    else:
        print("Proxmark3 не найден")
    print("Перейдите на ./register для получения секретного ключа.\n")

# Событие остановки приложения
@app.on_event("shutdown")
async def on_shutdown():
    # smth
    print("\nПриложение успешно остановлено.\n")

# Асинхронная задача для эмулятора двери
async def run_tkinter():
    root = tk.Tk()
    root.title("Эмулятор")
    root.geometry("150x150")
    root.configure(bg="red")
    root.attributes("-topmost", True)
    set_root(root)

    while True:
        while not task_queue.empty():
            task = task_queue.get()
            task()
        root.update()
        await asyncio.sleep(0.1)


# Асинхронная задача для сборки proxmark3
async def proxmark_build_task():
    if not shutil.which("make"):
        print('"make" не найдена. Сборка proxmark3 невозможна.')
    try:
        proxmark_build()
    except Exception as e:
        print(f"Ошибка сборки proxmark3: {e}")
    if not os.path.exists(proxmark.client_path):
        print("Неизвестная ошибка при инициализации или сборке proxmark3")
    print("Софт Proxmark3 был успешно собран!")
    await start_reader_task()
    await run_tkinter()
    print("Перезапустите приложение для работы Proxmark3")



# Асинхронная задача для старта proxmark3
async def start_reader_task():
    # await asyncio.to_thread(proxmark_build)
    await asyncio.to_thread(start_reader)


# Обработчики ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return render_error_page(request, 500, "Internal Server Error")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code in [404, 401, 403, 502, 503, 504]:
        error_map = {
            404: "Not Found",
            401: "Unauthorized",
            403: "Forbidden",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
        }
        message = error_map.get(exc.status_code, "Unknown Error Code")
        return render_error_page(request, exc.status_code, message)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail or "An error occurred"},
    )

