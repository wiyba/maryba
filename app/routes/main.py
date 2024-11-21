from app.main import app
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@app.get("/")
async def root():
    return FileResponse("templates/main.html")