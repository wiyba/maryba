from app.api.auth import *

from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/gallery")
async def gallery(request: Request):
    get_current_user(request)
    with open("templates/gallery.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)