import os
import json
import bcrypt

class Config:
    # Основная директория проекта
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # Путь к корню проекта

    # Директории для шаблонов и статики
    TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")  # Папка с шаблонами
    STATIC_DIR = os.path.join(BASE_DIR, "static")  # Папка со статикой

    # Поддиректории внутри static/
    IMAGES_DIR = os.path.join(STATIC_DIR, "images")  # Папка с изображениями
    VIDEOS_DIR = os.path.join(STATIC_DIR, "videos")  # Папка с видео
    TS_DIR = os.path.join(STATIC_DIR, "ts") # Папка с TS
    JS_DIR = os.path.join(STATIC_DIR, "js")  # Папка с JS
    STYLE_DIR = os.path.join(STATIC_DIR, "style")  # Папка с CSS

    # Пути к отдельным файлам
    FUNNY_VIDEO = os.path.join(VIDEOS_DIR, "harehareukaidansu.mp4")  # Путь к видео

    # Остальные ссылки
    DATABASE = os.path.join(BASE_DIR, "users.db")  # Путь к базе данных
    SESSION_SECRET = os.urandom(64)  # Секрет для сессий
    SECURITY_KEY = os.urandom(16).hex()  # Секрет для регистрации


class Password:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode(), hashed.encode())

class Camera:
    # User
    ip = '192.168.207.71'
    user = 'admin'
    passwd = 'rubetek11'
    rtsp_url = f"rtsp://{user}:{passwd}@{ip}:8554/Streaming/Channels/101"

    # Static
    ffmpeg_process = None
    streaming_active = False
    camera_check_task = None

config = Config()
verify_password = Password()
onvif = Camera()