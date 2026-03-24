from starlette.templating import Jinja2Templates

from app.settings import config

templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
