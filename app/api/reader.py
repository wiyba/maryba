import re
import subprocess

from app.settings import reader


class SerialReader:
    def __init__(self, port=None, value_block=None, key=None):
        self.port = port or reader.device_port
        self.value_block = value_block or reader.value_block
        self.key = key or reader.key

    def execute(self, command):
        try:
            process = subprocess.Popen(
                ["pm3", "-p", self.port, "-c", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            output, error = process.communicate(timeout=10)
            if process.returncode != 0:
                return None, error.strip()
            if not output.strip():
                return None, "идентификатор не найден"
            return output.strip(), None
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            return None, "timed out"
        except Exception as e:
            return None, str(e)

    def read_uid(self):
        output, error = self.execute("hf 14a read")
        if error or not output:
            return None, error or "nothing"
        match = re.search(r"UID:\s*([A-F0-9 ]+)", output)
        if match:
            return match.group(1).strip(), None
        return None, "no uid was found"

    def read_balance(self):
        output, error = self.execute(
            f"hf mf value --blk {self.value_block} -k {self.key} --get"
        )
        if error or not output:
            return None, error or "nothing"
        match = re.search(r"\[.\]\s*Dec\s*\.+\s*:\s*(\d+)", output)
        if match:
            return int(match.group(1)), None
        return None, "Balance not found"

    def read_card(self):
        output, error = self.execute(
            f"hf 14a read; hf mf value --blk {self.value_block} -k {self.key} --get"
        )
        if error or not output:
            return None, None, error or "nothing"
        uid_match = re.search(r"UID:\s*([A-F0-9 ]+)", output)
        bal_match = re.search(r"\[.\]\s*Dec\s*\.+\s*:\s*(\d+)", output)
        uid = uid_match.group(1).strip() if uid_match else None
        balance = int(bal_match.group(1)) if bal_match else None
        if not uid:
            return None, None, "no uid was found"
        return uid, balance, None

    def write_balance(self, value):
        output, error = self.execute(
            f"hf mf value --blk {self.value_block} -k {self.key} --set {value}"
        )
        if error:
            return False, error
        if output and "success" in output.lower():
            return True, None
        return False, output or "nothing"


class OSDPReader:
    pass
