import os
import sqlite3
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.api.auth import auth
from app.settings import config

router = APIRouter()


@router.get("/gallery")
async def gallery(request: Request):
    auth.get_current_user(request)
    with open("templates/gallery.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/api/events")
async def get_events(request: Request):
    auth.get_current_user(request)

    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, uid, username, event_type, balance, video_path, is_suspicious
        FROM events ORDER BY timestamp DESC LIMIT 100
    """)

    labels = {
        "success": "Успешный проход",
        "suspicious": "Подозрительный проход",
        "warning": "Очень подозрительный проход",
        "banned": "Заблокироавнный проход",
        "invalid_card": "Невалидный идентификатор",
        "manual": "Ручное сохранение",
    }

    events = []
    for row in cursor.fetchall():
        (
            event_id,
            timestamp,
            uid,
            username,
            event_type,
            balance,
            video_path,
            is_suspicious,
        ) = row
        events.append(
            {
                "id": event_id,
                "timestamp": timestamp,
                "datetime": datetime.fromtimestamp(timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "uid": uid,
                "username": username or "Неизвестно",
                "event_type": event_type,
                "event_label": labels.get(event_type, event_type),
                "balance": balance,
                "video_path": video_path,
                "is_suspicious": bool(is_suspicious),
            }
        )

    conn.close()
    return JSONResponse(events)


@router.get("/video/{date}/{filename}")
async def get_video(date: str, filename: str):
    video_path = os.path.join(config.BASE_DIR, "static", "recordings", date, filename)
    if not os.path.exists(video_path):
        return JSONResponse({"error": "Video not found"}, status_code=404)
    return FileResponse(
        video_path, media_type="video/mp4", headers={"Accept-Ranges": "bytes"}
    )
