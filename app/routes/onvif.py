from app.api.auth import *
from app.api.onvif import *

from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse

router = APIRouter()

# Страница из шаблона /templates/onvif.html
# Проверяет, что пользователь авторизован перед показом шаблона и картинки с камеры
# Эта страница нужна для сформатированного показа исходника изображения с камеры
@router.get("/onvif")
async def onvif_get(request: Request):
    get_current_user(request)
    with open("templates/onvif.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

# Роут для необработанной передачи кадров потока с IP ONVIF камеры в браузер. Получение картинки происходит в скрипте /app/api/onvif.py
@router.get("/onvif_video")
async def video_endpoint(request: Request):
    get_current_user(request)
    return StreamingResponse(
        video_stream(request),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )