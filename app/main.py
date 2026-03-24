# к сведению - все прогонялось через basedpyright (форматер)
# поэтому код может выглядеть слишком ровно
import asyncio
import os
from contextlib import asynccontextmanager

# nix-shell
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.api.onvif import get_camera, init_camera
from app.database import init_db
from app.routes import auth, gallery, main, onvif, profile, security
from app.settings import config, reader
from app.utils.charge import start_reader, stop_reader
from app.utils.exceptions import render_error_page
from app.utils import relay


@asynccontextmanager
async def lifespan(application):
    init_db()
    init_camera()
    relay.on()

    if os.path.exists(reader.device_port):
        asyncio.create_task(asyncio.to_thread(start_reader))
        print("ReaderManager: считыватель подключен")
    else:
        print("ReaderManager: считыватель не найден")

    yield

    stop_reader()
    relay.cleanup()
    cam = get_camera()
    if cam:
        cam.stop()


app = FastAPI(lifespan=lifespan)
app.include_router(main.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(onvif.router)
app.include_router(gallery.router)
app.include_router(security.router)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
app.mount("/images", StaticFiles(directory=config.IMAGES_DIR), name="images")
app.mount("/videos", StaticFiles(directory=config.VIDEOS_DIR), name="videos")
app.mount("/js", StaticFiles(directory=config.JS_DIR), name="js")
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET,
    session_cookie="my_session",
    https_only=False,
    same_site="lax",
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return render_error_page(request, 500, "Internal Server Error")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_map = {
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
    }
    if exc.status_code in error_map:
        return render_error_page(request, exc.status_code, error_map[exc.status_code])
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail or "Ошибка"}
    )
