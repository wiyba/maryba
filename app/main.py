# Импорты основных библиотек
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

# Импорты дополнительных библиотек
import asyncio
import shutil

# Импорты встроенных скриптов
from app import *
from app.utils.charge import *
from app.utils.exceptions import *
from app.api.reader import *

app = FastAPI()

# Подключение шаблонов и статических файлов
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR, html=True), name="static")
app.mount("/images", StaticFiles(directory=config.IMAGES_DIR, html=True), name="images")
app.mount("/videos", StaticFiles(directory=config.VIDEOS_DIR, html=True), name="videos")
app.mount("/js", StaticFiles(directory=config.JS_DIR, html=True), name="js")

# Настройка middleware для куки сессий
app.add_middleware(
    SessionMiddleware,
    secret_key=os.urandom(64),
    session_cookie="my_session",
    https_only=True,
    same_site="strict",
)

#################################################################################
@app.on_event("startup")
async def on_startup():
    database.init_db()
    from app.routes import main, auth, profile, onvif, gallery
    app.include_router(main.router)
    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(onvif.router)
    app.include_router(gallery.router)
    print("\nМодули успешно импортированы.")
    if reader.device_name != '' and os.path.exists(reader.client_path):
        asyncio.create_task(start_reader_task())
        print("Считыватель подключен\n")
    elif not os.path.exists(reader.client_path):
        print("Клиент считывателя не найден")
        ans = int(input("Хотите ли собрать его сейчас? [0-1]: "))
        if ans == 1:
            asyncio.create_task(reader_build_task())
        else:
            print("Продолжаем без считывателя...\n")
    else:
        print("Считыватель не найден\n")
#################################################################################
@app.on_event("shutdown")
async def on_shutdown():
    print("\nПриложение успешно остановлено.\n")
#################################################################################



# Асинхронная задача для сборки софта считывателя
async def reader_build_task():
    if not shutil.which("make"):
        print('"make" не найдена. Сборка софта для считывателя невозможна.')
    try:
        proxmark_build()
    except Exception as e:
        print(f"Ошибка сборки софта для считывателя: {e}")
    if not os.path.exists(reader.client_path):
        print("Неизвестная ошибка при инициализации или сборке proxmark3")
    print("Софт считывателя был успешно собран!")
    await start_reader_task()
    print("Перезапустите приложение для работы считывателя")



# Асинхронная задача для старта proxmark3
async def start_reader_task():
    await asyncio.to_thread(start_reader)

async def start_onvif_task():
    await asyncio.to_thread(start_onvif_task)


# Обработчики ошибок для отображения кастомных шаблонов при их появлении
# Отдельный обработчик для ошибки 500 так как сервер не даст загрузить шаблон при подобной ошибке в обычном случае
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return render_error_page(request, 500, "Internal Server Error")

# Обработчик для остальных популярных ошибок
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
        message = error_map.get(exc.status_code, "Неизвестный код ошибки")
        return render_error_page(request, exc.status_code, message)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail or "Произошла ошибка"},
    )

