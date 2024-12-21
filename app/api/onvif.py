from app import onvif

from fastapi import Request

import cv2
import subprocess

ffmpeg_process_video = None
streaming_active = False

# Функция для проверки доступности камеры
# Отправляет RTSP запрос через ffmpeg и проверяет, можно ли получить поток
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
            print(f"Вывод ffmpeg: {result.stderr.decode()}")
            return False
        print("Камера доступна")
        return True
    except subprocess.TimeoutExpired:
        print("Таймаут проверки камеры")
        return False
    except Exception as e:
        print(f"Ошибка при проверке доступности камеры: {e}")
        return False

# Асинхронная функция для запуска процесса ffmpeg
async def start_ffmpeg():
    global ffmpeg_process_video, streaming_active
    print("Начинаем поток ffmpeg...")

    # Проверка доступность камеры перед запуском
    if not check_camera_availability():
        print("Камера недоступна")
        stop_ffmpeg()
        return

    # Запуск потока ffmpeg на udp://127.0.0.1:1234 с указанными параметрами
    if ffmpeg_process_video is None or ffmpeg_process_video.poll() is not None:
        print("Запускаем процесс ffmpeg...")
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

            print("Процесс ffmpeg был успешно запущен")
        except Exception as e:
            print(f"Не удалось начать процесс ffmpeg: {e}")
            ffmpeg_process_video = None
            return

    streaming_active = True

# Функция для остановки процесса ffmpeg
# Проверяет активен ли процесс, завершает его корректно или убивает в случае ошибки
# Устанавливает переменные статуса потока в False
def stop_ffmpeg():
    global ffmpeg_process_video, streaming_active
    if ffmpeg_process_video and ffmpeg_process_video.poll() is None:
        try:
            print("Останавливаем процесс ffmpeg...")
            ffmpeg_process_video.terminate()
            ffmpeg_process_video.wait(timeout=5)
            print("Процесс ffmpeg был успешно завершен")
        except subprocess.TimeoutExpired:
            print("ffmpeg не удалось завершить вовремя. Пробуем kill()")
            ffmpeg_process_video.kill()
            print("Процесс ffmpeg был убит")
        except Exception as e:
            print(f"Ошибка при завершении ffmpeg: {e}. Пробуем kill()")
            ffmpeg_process_video.kill()
            print("Процесс ffmpeg был убит")
    else:
        print("Процесс ffmpeg уже завершен")
    ffmpeg_process_video = None
    streaming_active = False

# Асинхронная функция для обработки видеопотока
async def video_stream(request: Request):
    global streaming_active

    # Проверка статуса потока и запуск по необходимости
    if not streaming_active:
        await start_ffmpeg()

    if not streaming_active:
        print("Поток не был начат, камера недоступна")
        return

    # Считывает данные из видеопотока с помощью OpenCV и отдает кадры клиенту
    # В случае ошибки или отключения клиента завершает поток и освобождает ресурсы
    cap = cv2.VideoCapture("udp://127.0.0.1:1234")

    if not cap.isOpened():
        print("Не удалось открыть поток, остановка ffmpeg")
        stop_ffmpeg()
        return

    print("Поток был успешно запущен через OpenCV.")

    try:
        while True:
            if await request.is_disconnected():
                print("Пользователь отключился, останавливаем поток")
                break

            ret, frame = cap.read()
            if not ret:
                print("Не удалось получить кадр, останавливаем поток")
                break

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Не удалось энкодировать кадр")
                continue

            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    except Exception as e:
        print(f"Ошибка обработки потока: {e}")

    finally:
        cap.release()
        stop_ffmpeg()
        print("Поток был успешно завершен")
