from app.api.proxmark import execute_read
import os
import time

# Скрипт для чтения информации с проксмарка и последующего открытия двери
def start_reader():
    while True:
        if not os.path.exists("./app/api/new-magic4pm3/client/proxmark3"):
            print("Билд proxmark3 отсутствует: функция считывателя не была загружена.")
            print()
            break

        print("Ожидание метки...")
        output, error = execute_read("hf 14a reader")

        if error:
            print("Ошибка при выполнении команды hf 14a reader:", error)
            break

        if "UID" in output or "Found" in output:
            print("Метка найдена:", output)
            print("Пробую списать проход...")
            charge_output, charge_error = execute_read("hf mfp charge")
            if charge_error:
                print("Ошибка при выполнении команды hf mfp charge:", charge_error)
                break

            if "ok" in charge_output.lower():
                print("Успешно списано:", charge_output)


                print("Дверь открыта!")
            else:
                print("Не удалось списать проход:", charge_output)

        time.sleep(1)

if __name__ == "__main__":
    start_reader()
