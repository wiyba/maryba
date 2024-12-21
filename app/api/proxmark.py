import os
import subprocess
from app.config import proxmark

# Ребилд софта для проксмарка
def proxmark_build():
    os.system('cd ./app/api/new-magic4pm3 && git submodule init && git submodule update && git pull origin vos5 && make -j client')


# Скрипт для взаимодействия с proxmark3 и считывания ключкарты например
def execute_read(command):
    try:
        process = subprocess.Popen(
            [proxmark.client_path, "-p", proxmark.device_port, "-c", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )


        output, error = process.communicate(timeout=10)

        if process.returncode != 0:
            return None, error.strip()

        if not output.strip():
            return None, "Карта не обнаружена"

        return output.strip(), None

    except subprocess.TimeoutExpired:
        return None, "Команда превысила тайм-аут"
    except Exception as e:
        return None, str(e)