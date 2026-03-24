import sqlite3
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.auth import auth
from app.settings import anomaly, config

router = APIRouter()


def get_level(reason, warnings):
    if warnings >= anomaly.max_warnings:
        return "ban"
    if reason:
        return "warn"
    return "safe"


@router.get("/security")
async def security(request: Request):
    auth.get_current_user(request)
    with open("templates/security.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/api/anomalies")
async def get_anomalies(request: Request):
    auth.get_current_user(request)

    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.uid, a.timestamp, a.reason, a.resolved, k.username, k.warnings
        FROM anomalies a LEFT JOIN keys k ON a.uid = k.uid
        ORDER BY a.timestamp DESC LIMIT 100
    """)

    anomalies_list = [
        {
            "id": r[0],
            "uid": r[1],
            "timestamp": r[2],
            "datetime": datetime.fromtimestamp(r[2]).strftime("%Y-%m-%d %H:%M:%S"),
            "reason": r[3],
            "resolved": bool(r[4]),
            "username": r[5] or "noname",
            "level": get_level(r[3], r[6] or 0),
        }
        for r in cursor.fetchall()
    ]

    conn.close()
    return JSONResponse(anomalies_list)


@router.get("/api/suspicious_events")
async def get_suspicious_events(request: Request):
    auth.get_current_user(request)

    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.timestamp, e.uid, e.username, e.event_type, e.balance, e.video_path, e.anomaly_reason, k.warnings
        FROM events e LEFT JOIN keys k ON e.uid = k.uid
        WHERE e.is_suspicious = 1
        ORDER BY e.timestamp DESC LIMIT 100
    """)

    events = [
        {
            "id": r[0],
            "timestamp": r[1],
            "datetime": datetime.fromtimestamp(r[1]).strftime("%Y-%m-%d %H:%M:%S"),
            "uid": r[2],
            "username": r[3] or "noname",
            "event_type": r[4],
            "balance": r[5],
            "video_path": r[6],
            "reason": r[7],
            "level": get_level(r[7], r[8] or 0),
        }
        for r in cursor.fetchall()
    ]

    conn.close()
    return JSONResponse(events)
