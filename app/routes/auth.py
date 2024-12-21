from app.api.auth import login_user, register_user, logout_user
from app.api.session import get_current_user
from app.config import config
from app.main import templates
import os
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from app.utils.gui import change_color

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        session_token = login_user(username, password)
    except ValueError as e:
        print(f"Ошибка регистрации: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    request.session['user'] = username
    request.session['token'] = session_token
    return RedirectResponse("/", status_code=302)

@router.get("/logout")
async def logout(request: Request):
    get_current_user(request)
    user = request.session.get('user')
    if user:
        logout_user(user)
    request.session.clear()
    return RedirectResponse("/")

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    config.SECURITY_KEY = os.urandom(16).hex()
    print(f"\n\nСекрет для регистрации: {config.SECURITY_KEY}\n\n")
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(username: str = Form(...), password: str = Form(...), security_key: str = Form(...)):
    try:
        register_user(username, password, security_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RedirectResponse("/login", status_code=302)

