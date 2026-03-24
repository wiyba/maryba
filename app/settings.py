import os


class Config:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    IMAGES_DIR = os.path.join(STATIC_DIR, "images")
    VIDEOS_DIR = os.path.join(STATIC_DIR, "videos")
    JS_DIR = os.path.join(STATIC_DIR, "js")
    DATABASE = os.path.join(BASE_DIR, "users.db")
    SESSION_SECRET = "s8per-Secretk3y-jUr7-d0nt-K11l-m3"  # вместо os.urandom(32) чтобы на(до) защите(ы) не крашилась сессия
    SECURITY_KEY = os.urandom(16).hex()
    GPIO_PIN = 17
    GPIO_CHIP = "/dev/gpiochip0"
    RELAY_DURATION = 5


class Camera:
    source = "rtsp://10.0.0.1:8554/cam"
    frame_width = 640
    frame_height = 480
    fps = 25
    jpeg_quality = 80
    buffer_duration = 60
    recordings_dir = "static/recordings"


class Reader:
    device_port = "/dev/ttyACM0"
    value_block = 4
    key = "FFFFFFFFFFFF"
    # можно легко добавить динамическую перезапись секторов для увеличения времени требуемого на копирование с устройств вроде flipper zero
    # proxmark3 все еще легко их прочитает


class Anomaly:
    enable = True
    interval = 10
    single_reader = True
    max_warnings = 5


config = Config()
camera = Camera()
reader = Reader()
anomaly = Anomaly()
