from app import proxmark

import os
import subprocess

# Скрипт для взаимодействия с proxmark3 и считывания ключкарты например
def execute_read(command):
    try:
        # При вызове функции выполнится команда proxmark.client_path, "-p", proxmark.device_port, "-c", command, ее вывод будет захвачен через stdout и stderr в виде текста
        process = subprocess.Popen(
            [proxmark.client_path, "-p", proxmark.device_port, "-c", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # С таймаутом 10 секнуд будет ожидание окончания выполнения команды и последующее присвоение output и error результата выполнения stdout и stderr соответственно
        output, error = process.communicate(timeout=10)

        # Если код завершения не 0, то есть команда выполнилась с ошибками, то возвращается None и сообщение ошибки
        if process.returncode != 0:
            return None, error.strip()

        # Если вывод пустой, то возвращает None и ошибку о том, что карта не обнаружена
        if not output.strip():
            return None, "Карта не обнаружена"

        # Если вывод есть, то возвращает его и ошибку None
        return output.strip(), None

    # Если subprocess достигает таймаута то возвращает ошибку об этом
    except subprocess.TimeoutExpired:
        return None, "Команда превысила тайм-аут"
    # Возврат любой другой ошибки
    except Exception as e:
        return None, str(e)
