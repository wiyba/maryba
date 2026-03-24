import os

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.api.auth import auth
from app.routes import templates
from app.settings import config

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        session_token = auth.login(username, password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    request.session["user"] = username
    request.session["token"] = session_token
    return RedirectResponse("/", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    user = auth.get_current_user(request)
    auth.logout(user)
    request.session.clear()
    return RedirectResponse("/")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    config.SECURITY_KEY = os.urandom(16).hex()
    print(f"\nСекрет для регистрации: {config.SECURITY_KEY}\n")
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register(
    username: str = Form(...), password: str = Form(...), security_key: str = Form(...)
):
    try:
        auth.register(username, password, security_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    config.SECURITY_KEY = os.urandom(16).hex()
    return RedirectResponse("/login", status_code=302)


@router.get("/session_status", response_class=JSONResponse)
async def session_status(request: Request):
    user = auth.check_session(request)
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "username": user}
