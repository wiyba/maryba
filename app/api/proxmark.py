import os
import pexpect

def proxmark_repo():
    os.system('cd ./app/api/new-magic4pm3')
    os.system('git pull')

    os.system('make -j client')

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
