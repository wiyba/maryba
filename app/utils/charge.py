import re
from app.api.proxmark import execute_read
from app.config import config
import sqlite3
import os
import time


# Получение никнейма
def get_user_by_uid(uid):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM proxmark WHERE uid = ?", (uid,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return None

# Получение UID и баланса
def update_counter(uid, balance):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT counter FROM proxmark WHERE uid = ?", (uid,))
    result = cursor.fetchone()

    if result:
        cursor.execute("UPDATE proxmark SET counter = ? WHERE uid = ?", (balance, uid))
    else:
        cursor.execute("INSERT INTO proxmark (uid, counter) VALUES (?, ?)", (uid, balance))

    conn.commit()
    conn.close()

# Извлечение UID
def extract_uid(output):
    match = re.search(r"UID:\s*([A-F0-9 ]+)", output)
    if match:
        return match.group(1).strip()
    return None

# Извлечение баланса
def extract_balance(output):
    match = re.search(r"New balance:\s*([0-9A-F]+)", output)
    if match:
        return int(match.group(1), 16)
    return None


def start_reader():
    while True:
        if not os.path.exists("./app/api/new-magic4pm3/client/proxmark3"):
            print("Билд proxmark3 отсутствует: функция считывателя не была загружена.")
            print()
            break

        # print("Ожидание метки...") (для отладки)
        output, error = execute_read("hf 14a read")

        if error:
            if error == "Карта не обнаружена":
                print("Метка отсутствует, продолжаю сканировать...")
                time.sleep(1)
                continue
            print("Ошибка при выполнении команды hf 14a read:", error)
            break

        if output:
            uid = extract_uid(output)
            if uid:
                print(f"Метка найдена: {uid}")
            else:
                print("Не удалось найти UID в выводе.")
                continue

            # Проверяем UID в базе данных
            username = get_user_by_uid(uid)
            if username:
                print(f"Метка найдена: {uid}, Пользователь: {username}")
            else:
                print(f"Метка {uid} невалидная.")
                continue

            print("Пробую списать проход...")
            charge_output, charge_error = execute_read("hf mfp recharge --bal 1")
            if charge_error:
                print("Ошибка при выполнении команды hf mfp recharge:", charge_error)
                break

            if charge_output and "ok" in charge_output.lower():
                print("Успешно списано:", charge_output)

                balance = extract_balance(charge_output)
                if balance is not None:
                    print(f"Новый баланс: {balance}")
                    print("Обновление счетчика для UID:", uid)
                    update_counter(uid, balance)
                else:
                    print("Не удалось извлечь баланс из вывода.")




                    print("Дверь открыта!")
                    time.sleep(3)
            else:
                print("Не удалось списать проход:", charge_output or "Нет данных")
        time.sleep(0.5)


if __name__ == "__main__":
    start_reader()