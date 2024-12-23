from app.api.proxmark import *
from app.utils.gui import *
from app import config

import sqlite3
import time
import re


# Получение никнейма из датабазы используя полученный из вывода UID
def get_user_by_uid(uid):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()

    # Выводит значение столбца username в таблице proxmark из той строчки где uid равен полученному при выводе
    cursor.execute("SELECT username FROM proxmark WHERE uid = ?", (uid,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    return None

# Обновление счетчика проходов
def update_counter(uid, balance):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()

    # Обновляет значение таблицы proxmark в столбце counter в строчке где uid равен полученному при выводе
    cursor.execute("UPDATE proxmark SET counter = ? WHERE uid = ?", (balance, uid))

    conn.commit()
    conn.close()

# Извлечение UID из вывода для функции ниже
def extract_uid(output):
    match = re.search(r"UID:\s*([A-F0-9 ]+)", output)
    if match:
        return match.group(1).strip()
    return None

# Извлечение баланса из вывода для функции ниже
def extract_balance(output):
    match = re.search(r"New balance:\s*([0-9A-F]+)", output)
    if match:
        return int(match.group(1), 16)
    return None

# Функция для исполнения команд в cli proxmark3 используя апи из ./api/proxmark.py
def start_reader():
    while True:
        # Данный цикл бесконечно выполняет hf 14a read пока команда не даст вывод в output
        output, error = execute_read("hf 14a read")

        # Если error становится чем либо то это сигнализирует об ошибке и делает отладочный вывод
        if error:
            print("Ошибка при выполнении команды hf 14a read:", error)
            break

        # Если output становится чем либо, то производится извлечение UID и имени пользователя к которому он привязан.
        # После извлечения баланс карты пополняется на один (баланс это количество проходов).
        if output:
            uid = extract_uid(output)
            print(f"Метка найдена: {uid}")
            username = get_user_by_uid(uid)

            # Если в датабазе будет найден юзернейм то выведется отладочное сообщение с никнеймом и UID
            # Если в датабазе не будет найдена строка с получемнным UID то цикл чтения продолжится
            if username:
                print(f"Метка найдена: {uid}, Пользователь: {username}")
            else:
                print(f"Метка {uid} невалидная.")
                continue

            # После проверки юзернейма произведется пополнение баланса на 1
            charge_output, charge_error = execute_read("hf mfp recharge --bal 1")
            # charge_output = "ok New balance: 1 "
            # charge_error = None
            if charge_error:
                print("Ошибка при выполнении команды hf mfp recharge:", charge_error)
                continue

            # Если команда была успешно выполнена то
            if charge_output and "ok" in charge_output.lower():
                # Из вывода выполненных команд извлекается баланс
                balance = extract_balance(charge_output)
                print(f"Количество проходов: {balance}")
                update_counter(uid, balance)
                # Меняется цвет эмулятора двери, сигнализируя о том что дверь открыта
                change_color()
                print("Дверь открыта!")
                time.sleep(2.3)

            # Если charge_output будет какая либо другая ошибка то будет данный отладочный вывод
            else:
                print("Не удалось добавить проход:", charge_output or "Нет данных")