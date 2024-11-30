from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
import asyncio
import os
import shutil

from app.config import config
from app.utils.exceptions import render_error_page
from app.utils.charge import start_reader
from app.api.proxmark import proxmark_build

app = FastAPI()

# Подключение шаблонов и статических файлов
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR, html=True), name="static")
app.mount("/images", StaticFiles(directory=config.IMAGES_DIR, html=True), name="images")
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
    print("Перейдите на ./register для получения секретного ключа.\n")

# Событие остановки приложения
@app.on_event("shutdown")
async def on_shutdown():
    print("Приложение успешно остановлено.")

# Асинхронная задача для сборки proxmark3
async def handle_proxmark_build_task():
    if not shutil.which("make"):
        print('"make" не найдена. Сборка proxmark3 невозможна.')
        return
    try:
        await proxmark_build()
    except Exception as e:
        print(f"Ошибка сборки proxmark3: {e}")
    await asyncio.to_thread(start_reader)

# Обработчики ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return render_error_page(request, 500, "Internal Server Error")

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
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

# Логгирование в онлайн
@app.get("/logs", response_class=PlainTextResponse)
async def get_logs():
    try:
        with open("server.log", "r", encoding="utf-8") as log_file:
            return log_file.read()
    except FileNotFoundError:
        return "Лог файл не найден."
