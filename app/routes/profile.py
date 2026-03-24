import asyncio
import sqlite3

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.api.auth import auth
from app.routes import templates
from app.settings import config
from app.utils import relay
from app.utils.charge import pause_reader, resume_reader, serial, serial_lock

router = APIRouter()


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    auth.get_current_user(request)
    return templates.TemplateResponse("profile.html", {"request": request})


@router.post("/profile")
async def update_uid(request: Request, uid: str = Form(...)):
    try:
        auth.submit_uid(auth.get_current_user(request), uid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RedirectResponse("/", status_code=302)


@router.delete("/profile")
async def delete_profile(request: Request):
    user = auth.get_current_user(request)
    auth.logout(user)
    auth.delete(user)
    return RedirectResponse(url="/", status_code=303)


@router.post("/api/write_card")
async def write_card(request: Request):
    username = auth.get_current_user(request)

    pause_reader()
    await asyncio.sleep(0.3)

    relay.off()
    try:
        uid = None
        for i in range(50):
            with serial_lock:
                found_uid, _ = serial.read_uid()
            if found_uid:
                uid = found_uid
                break
            await asyncio.sleep(0.2)

        if not uid:
            raise HTTPException(
                status_code=400, detail="Карта не обнаружена за 10 секунд"
            )

        with serial_lock:
            success, error = serial.write_balance(0)

        if not success:
            raise HTTPException(status_code=500, detail=f"Ошибка записи: {error}")

        conn = sqlite3.connect(config.DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE keys SET uid = ?, counter = 0, warnings = 0 WHERE username = ?",
            (uid, username),
        )
        conn.commit()
        conn.close()

        asyncio.get_event_loop().call_later(5, relay.on)
        asyncio.get_event_loop().call_later(5, resume_reader)
        return JSONResponse({"uid": uid, "counter": 0})
    except Exception:
        relay.on()
        resume_reader()
        raise
