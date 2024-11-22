from app.config import onvif
import cv2
import subprocess
from fastapi import Request

ffmpeg_process = None
streaming_active = False

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



# Функция для запуска ffmpeg
async def start_ffmpeg():
    global ffmpeg_process, streaming_active
    print("Проверка доступности камеры...")

    if not check_camera_availability():
        stop_ffmpeg()
        return

    if ffmpeg_process is None or ffmpeg_process.poll() is not None:
        print("Запуск ffmpeg...")
        ffmpeg_process = subprocess.Popen([
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
        streaming_active = True




def stop_ffmpeg():
    global ffmpeg_process, streaming_active
    if isinstance(ffmpeg_process, subprocess.Popen):
        try:
            print("Остановка ffmpeg...")
            ffmpeg_process.terminate()
            ffmpeg_process.wait(timeout=5)
        except Exception as e:
            print(f"Ошибка при завершении ffmpeg: {e}. Пробуем kill()")
            ffmpeg_process.kill()
        finally:
            ffmpeg_process = None
            streaming_active = False
    else:
        print("Процесс ffmpeg не был запущен.")



# Функция ffmpeg
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


