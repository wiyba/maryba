from cryptography import x509
from cryptography.hazmat.backends import default_backend

import logging
import os
import ssl
import sys
import uvicorn

# Импорт настроек из файла settings.py, при наличии .env файла по пути /var/lib/maryba/ берет переменные из него
from settings import (DEBUG, UVICORN_HOST, UVICORN_PORT, UVICORN_SSL_CERTFILE,
                      UVICORN_SSL_KEYFILE, UVICORN_UDS)


### Функция логгера заимствована из https://github.com/Gozargah/Marzban ###
class LogToLogger:
    def __init__(self, logger, level, original_stream):
        self.logger = logger
        self.level = level
        self.original_stream = original_stream
        self.buffer = ''

    def write(self, message):
        if message:
            self.buffer += message
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                self.logger.log(self.level, line)

    def flush(self):
        if self.buffer:
            self.logger.log(self.level, self.buffer)
            self.buffer = ''
        self.original_stream.flush()

class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.getMessage() == '':
            return ''
        else:
            return super().format(record)

# Функция для настройки логгера
def setup_logger():
    logger = logging.getLogger("main_logger")
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    # Формат вывода
    formatter = CustomFormatter(
        "%(asctime)s == %(levelname)s: %(message)s", datefmt='%d.%m.%Y %H:%M:%S'
    )

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Файловый обработчик
    file_handler = logging.FileHandler("server.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Перенаправление print в логгер
    sys.stdout = LogToLogger(logger, logging.INFO, sys.__stdout__)
    sys.stderr = LogToLogger(logger, logging.ERROR, sys.__stderr__)

    # Настройка логгера Uvicorn
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers = logger.handlers
    uvicorn_access_logger.setLevel(logger.level)

    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.handlers = logger.handlers
    uvicorn_error_logger.setLevel(logger.level)

    return logger

logs = setup_logger()
#########################################################################

# Функция для проверки и валидации сертефикатов
def validate_cert_and_key(cert_file_path, key_file_path):
    if not os.path.isfile(cert_file_path):
        logs.error(f"SSL сертефикат по пути '{cert_file_path}' не существует.")
        raise ValueError(f"SSL сертефикат по пути '{cert_file_path}' не существует.")

    if not os.path.isfile(key_file_path):
        logs.error(f"SSL ключ по пути '{key_file_path}' не существует.")
        raise ValueError(f"SSL ключ по пути '{key_file_path}' не существует.")

    try:
        context = ssl.create_default_context()
        context.load_cert_chain(certfile=cert_file_path, keyfile=key_file_path)
    except ssl.SSLError as e:
        logs.error(f"Ошибка SSL: {e}")
        raise ValueError(f"Ошибка SSL: {e}")

    try:
        with open(cert_file_path, 'rb') as cert_file:
            cert_data = cert_file.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

        if cert.issuer == cert.subject:
            logs.warning("Предоставленный вами сертефикат не является доверенным.")
            raise ValueError("Предоставленный вами сертефикат не является доверенным.")
    except Exception as e:
        logs.error(f"Проверка сертефиката не удалась: {e}")
        raise ValueError(f"Проверка сертефиката не удалась: {e}")


# Основной процесс Uvicorn
if __name__ == "__main__":
    bind_args = {}

    if UVICORN_SSL_CERTFILE and UVICORN_SSL_KEYFILE:
        logs.info("Проверяем SSL сертефикаты...")
        validate_cert_and_key(UVICORN_SSL_CERTFILE, UVICORN_SSL_KEYFILE)

        bind_args['ssl_certfile'] = UVICORN_SSL_CERTFILE
        bind_args['ssl_keyfile'] = UVICORN_SSL_KEYFILE

        if UVICORN_UDS:
            bind_args['uds'] = UVICORN_UDS
        else:
            bind_args['host'] = UVICORN_HOST
            bind_args['port'] = UVICORN_PORT
    else:
        if UVICORN_UDS:
            bind_args['uds'] = UVICORN_UDS
        else:
            logs.warning("Запущено без SSL сертификатов. Доступ будет ограничен для localhost (127.0.0.1).")
            bind_args['host'] = '127.0.0.1'
            bind_args['port'] = UVICORN_PORT

    if DEBUG:
        bind_args['uds'] = None
        bind_args['host'] = '0.0.0.0'

    try:
        logs.info("Запускаем сервер Uvicorn...")
        logs.info("")
        uvicorn.run(
            "app.main:app",
            **bind_args,
            workers=1,
            reload=DEBUG,
            log_config=None,
            log_level=logging.DEBUG if DEBUG else logging.INFO
        )
    except FileNotFoundError as e:
        logs.error(f"При запуске произошла ошибка: {e}")