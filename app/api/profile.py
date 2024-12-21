from app import config

import sqlite3

# Изменение uid привязанного к пользвоателю в датабазе
def submit_uid(user: str, uid: str):
    conn = sqlite3.connect(config.DATABASE)
    cursor = conn.cursor()

    try:
        # Создание / Обновление столбца uid в строке с username как в переменной user до переданного в функцию
        cursor.execute("DELETE FROM proxmark WHERE username = ?", (user,))
        cursor.execute("INSERT INTO proxmark (username, uid) VALUES (?, ?)", (user, uid))
        conn.commit()
    # Так как в данной таблице параметры username и uid помечены как уникальные, при введении того UID что уже есть в таблице
    # будет вызвана IntegrityError и данная ошибка
    except sqlite3.IntegrityError:
        raise ValueError("Такой UID уже записан.")
    finally:
        conn.close()