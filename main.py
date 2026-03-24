import logging
import sys

import uvicorn

from settings import DEBUG


class LogToLogger:
    def __init__(self, logger, level, original_stream):
        self.logger = logger
        self.level = level
        self.original_stream = original_stream
        self.buffer = ""

    def write(self, message):
        if message:
            self.buffer += message
            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                if line:
                    self.logger.log(self.level, line)

    def flush(self):
        if self.buffer:
            self.logger.log(self.level, self.buffer)
            self.buffer = ""
        self.original_stream.flush()


def setup_logger():
    logger = logging.getLogger("main_logger")
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s == %(levelname)s: %(message)s", datefmt="%d.%m.%Y %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler("server.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    sys.stdout = LogToLogger(logger, logging.INFO, sys.__stdout__)
    sys.stderr = LogToLogger(logger, logging.ERROR, sys.__stderr__)

    for name in ("uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers = logger.handlers
        uv_logger.setLevel(logger.level)

    return logger


logs = setup_logger()

if __name__ == "__main__":
    logs.info("uvicorn starting......")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=80,
        workers=1,
        reload=DEBUG,
        log_config=None,
        log_level=logging.DEBUG if DEBUG else logging.INFO,
    )
