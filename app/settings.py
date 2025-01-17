import os

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

    # Остальные ссылки
    DATABASE = os.path.join(BASE_DIR, "users.db")  # Путь к базе данных
    SESSION_SECRET = os.urandom(64)  # Секрет для сессий
    SECURITY_KEY = os.urandom(16).hex()  # Секрет для регистрации


# Данные для подключения к onvif камере
class Camera:
    ip = '192.168.2.92'
    user = 'admin'
    passwd = 'rubetek11'
    rtsp_url = f"rtsp://{ip}:8554/Streaming/Channels/101"

    ffmpeg_process = None
    streaming_active = False
    camera_check_task = None

class Proxmark:
    device_name = os.popen('ls /dev/ | grep tty.usbmodem').read().strip() # Название устройства в системе (предположительно работает только на macos)
    client_path = "./app/api/new-magic4pm3/client/proxmark3" # Путь до клиента proxmark (приложения для взаимодействия)
    device_port = f"/dev/{device_name}" # Путь до proxmark

config = Config()
onvif = Camera()
proxmark = Proxmark()