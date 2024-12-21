from fastapi.responses import FileResponse
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    return FileResponse("templates/main.html")