from decouple import config
from dotenv import load_dotenv
import os

# TODO: Add cp func to setup.sh so .env file will be available at /var/lib/maryba
ENV_FILE_PATH = os.getenv('ENV_FILE_PATH', '/var/lib/maryba/.env')
load_dotenv(ENV_FILE_PATH)

UVICORN_HOST = config("UVICORN_HOST", default="127.0.0.1")
UVICORN_PORT = config("UVICORN_PORT", cast=int, default=8000)
UVICORN_UDS = config("UVICORN_UDS", default=None)
UVICORN_SSL_CERTFILE = config("UVICORN_SSL_CERTFILE", default=None)
UVICORN_SSL_KEYFILE = config("UVICORN_SSL_KEYFILE", default=None)

DEBUG = config("DEBUG", default=False, cast=bool)
DOCS = config("DOCS", default=False, cast=bool)