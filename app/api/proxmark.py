import os
import subprocess
import pexpect

# Ребилд софта для проксмарка
def proxmark_build():
    os.system('cd ./app/api/new-magic4pm3 && git submodule init && git submodule update && git pull origin vos5 && make -j client')



def execute_read(command):
    client_path = "./app/api/new-magic4pm3/client/proxmark3"
    device_port = "/dev/tty.usbmodemiceman1"

    if not os.path.exists(client_path):
        return None, f"Файл {client_path} не найден"

    try:
        process = subprocess.Popen(
            [client_path, "-p", device_port, "-c", command],
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