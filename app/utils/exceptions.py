from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from app.settings import config

env = Environment(loader=FileSystemLoader(config.TEMPLATES_DIR))


def render_error_page(request, status_code, error_type):
    template = env.get_template("error.html")
    content = template.render(request=request, number=status_code, type=error_type)
    return HTMLResponse(content=content, status_code=status_code)
