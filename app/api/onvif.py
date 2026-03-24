import asyncio
import os
import subprocess
import threading
from collections import deque
from datetime import datetime

import cv2

from app.settings import camera


class CameraManager:
    def __init__(self):
        self.cap = None
        self.frame = None
        self.buffer = deque(maxlen=int(camera.buffer_duration * camera.fps))
        self.frame_lock = threading.Lock()
        self.running = False
        os.makedirs(camera.recordings_dir, exist_ok=True)
        self._start_capture()

    def _start_capture(self):
        source = camera.source
        if isinstance(source, str) and source.startswith("rtsp://"):
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
            self.cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        else:
            self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera.frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, camera.fps)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"CameraManager: не удалось подключиться к {camera.source}"
            )
        self.running = True
        threading.Thread(target=self._capture_loop, daemon=True).start()
        print(f"CameraManager: подключено к {camera.source}")

    def _capture_loop(self):
        while self.running and self.cap:
            self.cap.grab()
            ret, frame = self.cap.retrieve()
            if ret:
                with self.frame_lock:
                    self.frame = frame
                    self.buffer.append(frame.copy())

    def get_frame(self):
        with self.frame_lock:
            return self.frame.copy() if self.frame is not None else None

    def save_buffer(self, filename):
        with self.frame_lock:
            frames = list(self.buffer)
        if not frames:
            return None
        date_folder = datetime.now().strftime("%Y-%m-%d")
        save_dir = os.path.join(camera.recordings_dir, date_folder)
        os.makedirs(save_dir, exist_ok=True)
        video_path = os.path.join(save_dir, f"{filename}.mp4")
        threading.Thread(
            target=self._save_video, args=(frames, video_path), daemon=True
        ).start()
        return video_path

    def _save_video(self, frames, video_path):
        try:
            height, width = frames[0].shape[:2]
            temp_path = video_path.replace(".mp4", "_temp.mp4")
            out = cv2.VideoWriter(
                temp_path, cv2.VideoWriter_fourcc(*"mp4v"), camera.fps, (width, height)
            )
            if not out.isOpened():
                return
            for frame in frames:
                out.write(frame)
            out.release()

            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    temp_path,
                    "-c:v",
                    "libx264",
                    "-preset",
                    "ultrafast",
                    "-y",
                    video_path,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                os.remove(temp_path)
            else:
                os.rename(temp_path, video_path)
        except Exception as e:
            print(f"CameraManager: ошибка сохранения - {e}")

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()


camera_manager = None


def init_camera():
    global camera_manager
    try:
        camera_manager = CameraManager()
    except Exception as e:
        print(f"CameraManager: {e}")


def get_camera():
    return camera_manager


async def video_stream(request):
    while True:
        if await request.is_disconnected():
            break
        if not camera_manager:
            await asyncio.sleep(1)
            continue
        frame = camera_manager.get_frame()
        if frame is None:
            await asyncio.sleep(0.1)
            continue
        ret, buffer = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, camera.jpeg_quality]
        )
        if not ret:
            continue
        yield (
            b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )
        await asyncio.sleep(1.0 / camera.fps)
