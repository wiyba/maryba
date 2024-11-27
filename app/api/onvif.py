from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import cv2
import subprocess
from app.config import onvif

# Глобальные переменные
ffmpeg_process_video = None
ffmpeg_process_audio = None
streaming_active = False

app = FastAPI()


# Проверка доступности камеры
def check_camera_availability():
    try:
        print("Проверка доступности камеры с помощью ffmpeg...")
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
            print("Камера недоступна. Остановка потока.")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("Проверка камеры завершилась по таймауту. Камера недоступна.")
        return False


# Функция для запуска FFmpeg потоков
async def start_ffmpeg():
    global ffmpeg_process_video, ffmpeg_process_audio, streaming_active
    print("Проверка доступности камеры...")

    if not check_camera_availability():
        stop_ffmpeg()
        return

    if ffmpeg_process_video is None or ffmpeg_process_video.poll() is not None:
        print("Запуск видео ffmpeg...")
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
            '-q', '5',
            'udp://127.0.0.1:1234'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    if ffmpeg_process_audio is None or ffmpeg_process_audio.poll() is not None:
        print("Запуск аудио ffmpeg...")
        ffmpeg_process_audio = subprocess.Popen([
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-i', onvif.rtsp_url,
            '-vn',  # Только аудио
            '-acodec', 'libmp3lame',
            '-f', 'mp3',
            'http://127.0.0.1:8001/audio'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    streaming_active = True


# Функция для остановки FFmpeg потоков
def stop_ffmpeg():
    global ffmpeg_process_video, ffmpeg_process_audio, streaming_active
    for process in [ffmpeg_process_video, ffmpeg_process_audio]:
        if isinstance(process, subprocess.Popen):
            try:
                print("Остановка ffmpeg...")
                process.terminate()
                process.wait(timeout=5)
            except Exception as e:
                print(f"Ошибка при завершении ffmpeg: {e}. Пробуем kill()")
                process.kill()
        process = None

    streaming_active = False


# Генерация видео потока для StreamingResponse
async def video_stream(request: Request):
    global streaming_active

    if not streaming_active:
        await start_ffmpeg()

    if not streaming_active:
        print("Поток не запущен, камера недоступна.")
        return

    cap = cv2.VideoCapture("udp://127.0.0.1:1234")

    if not cap.isOpened():
        print("Не удалось открыть поток видео. Остановка потока.")
        stop_ffmpeg()
        return

    try:
        while True:
            if await request.is_disconnected():
                print("Пользователь покинул страницу, останавливаем поток.")
                break

            ret, frame = cap.read()
            if not ret:
                print("Не удалось получить кадр. Остановка потока.")
                break

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    except Exception as e:
        print(f"Ошибка при обработке видео потока: {e}")

    finally:
        cap.release()
        stop_ffmpeg()
        print("Видео поток завершён.")


async def audio_stream():
    def generate():
        with subprocess.Popen([
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-i', onvif.rtsp_url,
            '-vn',
            '-acodec', 'libmp3lame',
            '-f', 'mp3',
            '-'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            while True:
                data = process.stdout.read(1024)
                if not data:
                    break
                yield data

    return StreamingResponse(generate(), media_type="audio/mpeg")
