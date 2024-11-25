import os
import pexpect

# Ребилд софта для проксмарка
def proxmark_build():
    os.system('cd ./app/api/new-magic4pm3 && git submodule init && git submodule update && git pull origin vos5 && make -j client')

# Использование команд для проксмарка
def execute_read(command):
    client_path = "./app/api/new-magic4pm3/client/proxmark3"
    device_port = "/dev/ttyACM0"

    if not os.path.exists(client_path):
        return None, f"Файл {client_path} не найден"

    try:
        session = pexpect.spawn(f"{client_path} -p {device_port}", timeout=10)
        session.expect("proxmark3>")
        session.sendline(command)
        session.expect("proxmark3>")
        output = session.before.decode('utf-8')
        session.sendline("exit")
        return output, None

    except pexpect.exceptions.ExceptionPexpect as e:
        return None, str(e)