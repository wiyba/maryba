import sqlite3
import threading
import time
from datetime import datetime

from app.api.onvif import get_camera
from app.api.reader import OSDPReader, SerialReader
from app.settings import config
from app.utils import relay
from app.utils.anomaly import detector

serial = SerialReader()
serial_lock = threading.Lock()
stop = False
paused = False


## нужны глобально для работы функции перезаписи ##
def stop_reader():
    global stop
    stop = True


def pause_reader():
    global paused
    paused = True


def resume_reader():
    global paused
    paused = False


#####################################################


def start_reader():
    while not stop:
        if paused:
            time.sleep(0.1)
            continue

        with serial_lock:
            uid, balance, error = serial.read_card()

        if error:
            continue

        print(" ")
        username = get_user_by_uid(uid)
        if not username:
            print(f"ReaderManager: невалидный идентификатор {uid}")
            log_event(uid, None, "invalid_card")
            continue

        if balance is None:
            print(f"ReaderManager: ошибка чтения баланса {uid}")
            continue

        print(f"ReaderManager: {uid} -> {username}")

        level, reason = detector.check(uid, username, balance)

        if level == "ban":
            print(f"AnomalyManager: {username} -> {uid} заблокирован")
            log_event(uid, username, "banned", balance, 1, reason)
            continue

        if level != "safe":
            print(f"AnomalyManager: {level} -> {reason}")

        conn = sqlite3.connect(config.DATABASE)
        stored = conn.execute(
            "SELECT counter FROM keys WHERE uid = ?", (uid,)
        ).fetchone()
        conn.close()
        db_value = stored[0] if stored else balance

        new_balance = db_value + 1

        with serial_lock:
            success, error = serial.write_balance(new_balance)

        if not success:
            print(f"ReaderManager: ошибка записи — {error}")
            continue

        update_counter(uid, new_balance)
        relay.off()

        if level == "warn":
            event_type = "warning"
        elif level == "suspicious":
            event_type = "suspicious"
        else:
            event_type = "success"

        print(f"ReaderManager: balance == {balance} -> {new_balance}")
        log_event(
            uid,
            username,
            event_type,
            new_balance,
            1 if level != "safe" else 0,
            reason if level != "safe" else None,
        )
        time.sleep(config.RELAY_DURATION)
        relay.on()


def get_user_by_uid(uid):
    conn = sqlite3.connect(config.DATABASE)
    row = conn.execute("SELECT username FROM keys WHERE uid = ?", (uid,)).fetchone()
    conn.close()
    return row[0] if row else None


def update_counter(uid, balance):
    conn = sqlite3.connect(config.DATABASE)
    conn.execute("UPDATE keys SET counter = ? WHERE uid = ?", (balance, uid))
    conn.commit()
    conn.close()


def log_event(
    uid, username, event_type, balance=None, is_suspicious=0, anomaly_reason=None
):
    conn = sqlite3.connect(config.DATABASE)
    timestamp = int(time.time())
    video_path = None

    cam = get_camera()
    if cam:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        video_path = cam.save_buffer(f"{ts}_{username or 'unknown'}_{event_type}")

    conn.execute(
        "INSERT INTO events (timestamp, uid, username, event_type, balance, video_path, is_suspicious, anomaly_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            timestamp,
            uid,
            username,
            event_type,
            balance,
            video_path,
            is_suspicious,
            anomaly_reason,
        ),
    )
    conn.commit()
    conn.close()
