from queue import Queue

root = None
task_queue = Queue()


def set_root(tk_root):
    global root
    root = tk_root


def change_color():
    task_queue.put(lambda: root.configure(bg="lime"))
    task_queue.put(lambda: root.after(3000, lambda: root.configure(bg="red")))
