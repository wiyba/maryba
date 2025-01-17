from app.api.profile import *
from app.api.auth import *
from app import templates

from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()

# Отображение шаблона /templates/profile.html
@router.get("/profile", response_class=HTMLResponse)
async def register_page(request: Request):
    get_current_user(request)
    return templates.TemplateResponse("profile.html", {"request": request})

# При получени POST запроса изменяет UID в датабазе в соответствии с содержимым запроса, используя уже описанные мной функции.
@router.post("/profile")
async def register(request: Request, uid: str = Form(...)):
    try:
        submit_uid(get_current_user(request), uid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RedirectResponse("/", status_code=302)

# При получении DELETE запроса выполняет уже описанную мной функцию delete_user для удаления пользователя из датабазы, если аккаунт был успешно удален, то перенаправляет на страницу /
@router.delete("/profile")
async def delete_profile(request: Request):
    user = get_current_user(request)
    logout_user_req = logout_user(user)
    delete_user_req = delete_user(user)
    if not delete_user_req or not logout_user_req:
        raise HTTPException(status_code=404)
    return RedirectResponse(url="/", status_code=303)

