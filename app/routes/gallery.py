from app.main import app
from app.config import config
from app.api.session import get_current_user
from fastapi import Request, APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@app.get("/video")
async def video(request: Request):
    get_current_user(request)
    return FileResponse(config.FUNNY_VIDEO, media_type="video/mp4")