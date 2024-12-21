import queue

# Настройка окна и очереди
root = None
task_queue = queue.Queue()

# Тут переменная root объявляется глобальной, чтобы из других скриптов и функций можно было изменять цвет окна
def set_root(tk_root):
    global root
    root = tk_root

# После вызова этой функции выполняется лямбда функция, связанная с основной асинхронной функцией в /app/main.py
# Когда вызывается эта функция, в очередь заданий помещается две лямбда функции
# Цвет окна root меняется на лаймовый, и через 3 секунды он меняется обратно на красный
def change_color():
    task_queue.put(lambda: root.configure(bg="lime"))
    task_queue.put(lambda: root.after(3000, lambda: root.configure(bg="red")))
