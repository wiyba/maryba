import sqlite3
import time
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from app.api.auth import auth
from app.api.onvif import get_camera, video_stream
from app.settings import config

router = APIRouter()


@router.get("/onvif")
async def onvif_page(request: Request):
    auth.get_current_user(request)
    with open("templates/onvif.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/onvif_video")
async def video_endpoint(request: Request):
    auth.get_current_user(request)
    return StreamingResponse(
        video_stream(request), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.post("/save_replay")
async def save_replay(request: Request):
    user = auth.get_current_user(request)

    cam = get_camera()
    if not cam:
        return JSONResponse({"success": False, "error": "no cam"}, status_code=500)

    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    video_path = cam.save_buffer(f"{timestamp_str}_manual_{user}")

    if not video_path:
        return JSONResponse({"success": False, "error": "empty buf"}, status_code=500)

    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (timestamp, uid, username, event_type, balance, video_path) VALUES (?, ?, ?, ?, ?, ?)",
        (int(time.time()), None, user, "manual", None, video_path),
    )
    conn.commit()
    conn.close()

    return JSONResponse({"success": True, "path": video_path})
