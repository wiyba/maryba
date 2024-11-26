from app.config import config
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader


app = FastAPI()
env = Environment(loader=FileSystemLoader(config.TEMPLATES_DIR))

def render_error_page(request: Request, status_code: int, error_type: str) -> HTMLResponse:
    template = env.get_template("error.html")
    content = template.render(
        request=request,
        number=status_code,
        type=error_type,
    )
    return HTMLResponse(content=content, status_code=status_code)
