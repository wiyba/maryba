import os
import threading

from app.settings import config

request = None
lock = threading.Lock()
available = os.path.exists(config.GPIO_CHIP)


def init():
    global request
    if not available or request is not None:
        return
    try:
        import gpiod
        from gpiod.line import Direction, Value

        request = gpiod.request_lines(
            config.GPIO_CHIP,
            consumer="maryba-relay",
            config={
                config.GPIO_PIN: gpiod.LineSettings(
                    direction=Direction.OUTPUT, output_value=Value.INACTIVE
                )
            },
        )
        print("RelayManager: реле открыто")
    except Exception as e:
        print(f"RelayManager: реле недоступно -> {e}")


def on():
    if not available:
        return
    with lock:
        init()
        if request is None:
            return
        from gpiod.line import Value

        request.set_value(config.GPIO_PIN, Value.ACTIVE)


def off():
    if not available:
        return
    with lock:
        init()
        if request is None:
            return
        from gpiod.line import Value

        request.set_value(config.GPIO_PIN, Value.INACTIVE)


def cleanup():
    global request
    if request:
        try:
            from gpiod.line import Value

            request.set_value(config.GPIO_PIN, Value.INACTIVE)
            request.release()
        except Exception:
            pass
        request = None
