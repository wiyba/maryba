from app.main import app
from app.utils.gui import change_color
from app.api.session import get_current_user
from app.api.onvif import video_stream, check_camera_availability
from fastapi import Request, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

router = APIRouter()

@router.api_route("/onvif", methods=["GET", "POST"])
async def onvif(request: Request):
    get_current_user(request)

    if request.method == "POST":
        body = await request.json()
        change_color()



    with open("templates/onvif.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

@router.get("/onvif_video")
async def video_endpoint(request: Request):
    get_current_user(request)
    return StreamingResponse(
        video_stream(request),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )