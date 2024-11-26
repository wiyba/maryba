from app.main import templates
from app.api.profile import submit_uid
from app.api.session import get_current_user
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()

@router.get("/profile", response_class=HTMLResponse)
async def register_page(request: Request):
    get_current_user(request)
    return templates.TemplateResponse("profile.html", {"request": request})

@router.post("/profile")
async def register(request: Request, uid: str = Form(...)):
    try:
        submit_uid(request, uid)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RedirectResponse("/", status_code=302)
