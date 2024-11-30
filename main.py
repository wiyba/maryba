import click
import logging
import os
import ssl
import sys
import uvicorn
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from settings import (DEBUG, UVICORN_HOST, UVICORN_PORT, UVICORN_SSL_CERTFILE,
                      UVICORN_SSL_KEYFILE, UVICORN_UDS)



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
                # Логируем каждую строку, включая пустые
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

def setup_logger():
    logger = logging.getLogger("main_logger")
    logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

    formatter = CustomFormatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt='%d.%m.%Y %H:%M:%S'
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





# Создание глобального logger
logger = setup_logger()


def validate_cert_and_key(cert_file_path, key_file_path):
    if not os.path.isfile(cert_file_path):
        logger.error(f"SSL certificate file '{cert_file_path}' does not exist.")
        raise ValueError(f"SSL certificate file '{cert_file_path}' does not exist.")

    if not os.path.isfile(key_file_path):
        logger.error(f"SSL key file '{key_file_path}' does not exist.")
        raise ValueError(f"SSL key file '{key_file_path}' does not exist.")

    try:
        context = ssl.create_default_context()
        context.load_cert_chain(certfile=cert_file_path, keyfile=key_file_path)
    except ssl.SSLError as e:
        logger.error(f"Ошибка SSL: {e}")
        raise ValueError(f"Ошибка SSL: {e}")

    try:
        with open(cert_file_path, 'rb') as cert_file:
            cert_data = cert_file.read()
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

        if cert.issuer == cert.subject:
            logger.warning("Предоставленный вами сертефикат не является доверенным.")
            raise ValueError("Предоставленный вами сертефикат не является доверенным.")
    except Exception as e:
        logger.error(f"Проверка сертефиката не удалась: {e}")
        raise ValueError(f"Проверка сертефиката не удалась: {e}")


if __name__ == "__main__":
    bind_args = {}

    if UVICORN_SSL_CERTFILE and UVICORN_SSL_KEYFILE:
        logger.info("Проверяем SSL сертефикаты...")
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
            logger.warning("ВАЖНО! Запущено без SSL сертификатов. Доступ будет ограничен для localhost (127.0.0.1).")
            bind_args['host'] = '127.0.0.1'
            bind_args['port'] = UVICORN_PORT

    if DEBUG:
        bind_args['uds'] = None
        bind_args['host'] = '0.0.0.0'

    try:
        logger.info("Запускаем сервер Uvicorn...")
        uvicorn.run(
            "app.main:app",
            **bind_args,
            workers=1,
            reload=DEBUG,
            log_config=None,
            log_level=logging.DEBUG if DEBUG else logging.INFO
        )
    except FileNotFoundError as e:
        logger.error(f"При запуске произошла ошибка: {e}")