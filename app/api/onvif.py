from app import *

from fastapi import Request, HTTPException
from fastapi.responses import StreamingResponse

import asyncio
import subprocess
import cv2

ffmpeg_process_video = None
streaming_active = False

def check_camera_availability():
    try:
        print("Проверяем доступность камеры...")
        result = subprocess.run(
            [
                'ffmpeg',
                '-rtsp_transport', 'tcp',
                '-i', onvif.rtsp_url,
                '-t', '3',
                '-f', 'null', '-'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        if result.returncode != 0:
            print("Камера недоступна, останавливаем поток")
            return False
        print("Камера доступна")
        return True
    except subprocess.TimeoutExpired:
        print("Таймаут проверки камеры")
        return False
    except Exception as e:
        print(f"Ошибка при проверке доступности камеры: {e}")
        return False

async def start_ffmpeg():
    global ffmpeg_process_video, streaming_active
    print("Начинаем поток ffmpeg...")

    if ffmpeg_process_video is None or ffmpeg_process_video.poll() is not None:
        try:
            ffmpeg_process_video = subprocess.Popen([
                'ffmpeg',
                '-rtsp_transport', 'tcp',
                '-fflags', 'nobuffer',
                '-flags', 'low_delay',
                '-analyzeduration', '1000000',
                '-probesize', '1000000',
                '-fflags', '+discardcorrupt',
                '-i', onvif.rtsp_url,
                '-f', 'mpegts',
                '-codec:v', 'mpeg1video',
                '-q:v', '5',
                '-r', '25',
                'udp://127.0.0.1:1234'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print("Процесс ffmpeg успешно запущен")
        except Exception as e:
            print(f"Ошибка запуска ffmpeg: {e}")
            ffmpeg_process_video = None
            return
    streaming_active = True

def stop_ffmpeg():
    global ffmpeg_process_video, streaming_active
    if ffmpeg_process_video and ffmpeg_process_video.poll() is None:
        try:
            print("Останавливаем ffmpeg...")
            ffmpeg_process_video.terminate()
            ffmpeg_process_video.wait(timeout=5)
            print("Процесс ffmpeg успешно завершен")
        except subprocess.TimeoutExpired:
            print("Не удалось завершить ffmpeg, убиваем процесс...")
            ffmpeg_process_video.kill()
            print("Процесс ffmpeg убит")
        except Exception as e:
            print(f"Ошибка при завершении ffmpeg: {e}")
            ffmpeg_process_video.kill()
    ffmpeg_process_video = None
    streaming_active = False

async def start_onvif_task():
    while True:
        try:
            print('test')
            camera_available = await asyncio.to_thread(check_camera_availability)

            if camera_available and not streaming_active:
                await start_ffmpeg()

            if not camera_available and streaming_active:
                stop_ffmpeg()


        except asyncio.CancelledError:
            print("Задача start_onvif_task отменена, завершаем...")
            stop_ffmpeg()
            break
        except Exception as e:
            print(f"Ошибка в start_onvif_task: {e}")


async def video_stream(request: Request):
    global streaming_active

    if not streaming_active:
        print("Поток неактивен, проверяем доступность камеры...")
        camera_available = await asyncio.to_thread(check_camera_availability)
        if camera_available:
            await start_ffmpeg()
        else:
            raise HTTPException(status_code=503)

    cap = cv2.VideoCapture("udp://127.0.0.1:1234")

    if not cap.isOpened():
        print("Не удалось открыть поток, останавливаем ffmpeg...")
        stop_ffmpeg()
        raise HTTPException(status_code=500)

    print("Поток успешно открыт через OpenCV.")

    try:
        while True:
            if await request.is_disconnected():
                print("Пользователь отключился, завершаем поток...")
                break

            ret, frame = cap.read()
            if not ret:
                print("Не удалось получить кадр, завершаем поток...")
                break

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Не удалось закодировать кадр")
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

            await asyncio.sleep(0.04)
    finally:
        cap.release()
        stop_ffmpeg()
        print("Поток завершён.")