from fastapi import Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from app.config import config

env = Environment(loader=FileSystemLoader(config.TEMPLATES_DIR))

# Функция для отображения шаблона ошибки с заданными данными об ошибке
def render_error_page(request: Request, status_code: int, error_type: str) -> HTMLResponse:
    template = env.get_template("error.html")
    content = template.render(
        request=request,
        number=status_code,
        type=error_type,
    )
    return HTMLResponse(content=content, status_code=status_code)
