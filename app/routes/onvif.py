from app.main import app
from app.api.session import get_current_user
from app.api.onvif import video_stream, audio_stream
from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse

router = APIRouter()

@app.get("/onvif")
async def onvif(request: Request):
    get_current_user(request)
    with open("templates/onvif.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

@app.get("/onvif_video")
async def video_endpoint(request: Request):
    get_current_user(request)
    return StreamingResponse(video_stream(request), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/onvif_audio")
async def audio_endpoint(request: Request):
    get_current_user(request)
    return await audio_stream()