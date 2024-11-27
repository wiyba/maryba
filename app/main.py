from app.config import config
from app.utils.exceptions import render_error_page
from app.utils.charge import start_reader
from app.api.proxmark import proxmark_build
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
import shutil
import os
import time
import asyncio

app = FastAPI()
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
app.mount("/favicon", StaticFiles(directory=config.IMAGES_DIR), name="favicon")
app.mount("/js", StaticFiles(directory=config.JS_DIR), name="js")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.urandom(64),
    session_cookie="my_session",
    https_only=True,
    same_site="strict"
)

# Выполняется при запуске
@app.on_event("startup")
async def startup():
    from app.database import init_db
    init_db()

    from app.routes import main, auth, profile, onvif, gallery
    app.include_router(main.router)
    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(onvif.router)
    app.include_router(gallery.router)

    print()
    print("Модули импортированы успешно")
    print("Вы получите секрет для регистрации при переходе на ./register")
    print()

    # asyncio.create_task(handle_proxmark_build_task()) (если необходимо забилдить proxmark3)

# Выполняется при остановке
@app.on_event("shutdown")
async def shutdown():
    print("Успешно остановлено")

# Билд софта для proxmark3
async def handle_proxmark_build_task():
    if not shutil.which("make"):
        print('"make" не найдена. Билд proxmark3 невозможен.')
        return
    try:
        await proxmark_build()
    except Exception as e:
        print(f"Ошибка при выполнении сборки proxmark3: {e}")
    await asyncio.to_thread(start_reader)

# Настройка кастомных страниц ошибок
@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception):
    return render_error_page(request, 500, "Internal Server Error")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return render_error_page(request, 404, "Not Found")
    elif exc.status_code == 401:
        return render_error_page(request, 401, "Unauthorized")
    elif exc.status_code == 403:
        return render_error_page(request, 403, "Forbidden")
    elif exc.status_code == 502:
        return render_error_page(request, 502, "Bad Gateway")
    elif exc.status_code == 503:
        return render_error_page(request, 503, "Service Unavailable")
    elif exc.status_code == 504:
        return render_error_page(request, 504, "Gateway Timeout")
    elif 100 >= exc.status_code >= 559:
        return render_error_page(request, exc.status_code, "Unknown Error Code")
    return HTMLResponse(
        content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>",
        status_code=exc.status_code,
    )

