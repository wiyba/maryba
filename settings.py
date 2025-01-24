import os
from pathlib import Path
from dotenv import load_dotenv
from decouple import config

env_file = os.getenv("ENV_FILE_PATH", "/var/lib/maryba/.env")
if Path(env_file).is_file():
    load_dotenv(env_file)
else:
    load_dotenv(".env.dev")

UVICORN_HOST = config("UVICORN_HOST", default="127.0.0.1")
UVICORN_PORT = config("UVICORN_PORT", cast=int, default=8000)
UVICORN_UDS = config("UVICORN_UDS", default=None)
UVICORN_SSL_CERTFILE = config("UVICORN_SSL_CERTFILE", default=None)
UVICORN_SSL_KEYFILE = config("UVICORN_SSL_KEYFILE", default=None)
DEBUG = config("DEBUG", default=True, cast=bool)
DOCS = config("DOCS", default=False, cast=bool)
