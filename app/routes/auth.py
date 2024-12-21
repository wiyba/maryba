from app.api.auth import *
from app import config, templates

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse

import os

router = APIRouter()

# Отображение страницы входа в аккаунт
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# При получении POST запроса выполняется данная функция, который использует уже описанные мной функции для входа в аккаунт
# POST запросы отправляются при подтверждении входа в аккаунт или при регистрации аккаунта
@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        session_token = login_user(username, password)
    except ValueError as e:
        print(f"Ошибка входа: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    request.session['user'] = username
    request.session['token'] = session_token
    return RedirectResponse("/", status_code=302)

# Для выхода из аккаунта выполняются также описанные мной функции get_current_user и logout_user
@router.get("/logout")
async def logout(request: Request):
    get_current_user(request)
    if get_current_user(request):
        logout_user(get_current_user(request))
    request.session.clear()
    return RedirectResponse("/")

# Отображение страницы регистрации, секрет для регистрации генерируется как раз при входе на эту страницу, то есть
# после получения GET запроса. Секрет отправляется в консоль и остается таким же до следующего GET запроса или успешной регистрации
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    config.SECURITY_KEY = os.urandom(16).hex()
    print(f"\n\nСекрет для регистрации: {config.SECURITY_KEY}\n\n")
    return templates.TemplateResponse("register.html", {"request": request})

# При получении POST запроса выполняется данная функция, которая также использует уже описанные мною функции.
# После успешной регистрации секрет регенерируется и никуда не отправляется, чтобы его нельзя было абузить.
# POST запросы отправляются при подтверждении входа в аккаунт или при регистрации аккаунта
@router.post("/register")
async def register(username: str = Form(...), password: str = Form(...), security_key: str = Form(...)):
    try:
        register_user(username, password, security_key)
    except ValueError as e:
        print(f"Ошибка регистрации: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    config.SECURITY_KEY = os.urandom(16).hex()
    return RedirectResponse("/login", status_code=302)

