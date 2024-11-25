from app.config import config
from app.utils.pm_charge import start_reader
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import asyncio

app = FastAPI()
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.urandom(64),
    session_cookie="my_session",
    https_only=True,
    same_site="strict"
)

@app.on_event("startup")
async def startup():
    from app.database import init_db
    init_db()
    from app.routes import main, auth, onvif, gallery
    app.include_router(main.router)
    app.include_router(auth.router)
    app.include_router(onvif.router)
    app.include_router(gallery.router)
    print("Модули импортированы успешно")
    print("Вы получите секрет для регистрации при переходе на ./register")
    asyncio.create_task(start_reader_task())

@app.on_event("shutdown")
async def shutdown():
    print("Успешно остановлено")

async def start_reader_task():
    await asyncio.to_thread(start_reader)
