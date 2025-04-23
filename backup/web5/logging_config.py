import os
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler


def configure_logging(app):
    """Настройка логирования для Flask приложения"""
    # Создаем директорию для логов, если ее нет
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Уровень логирования по умолчанию
    log_level = logging.DEBUG if app.debug else logging.INFO

    # Форматтеры
    base_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    detailed_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-20s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Обработчики
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(base_formatter)

    file_debug_handler = RotatingFileHandler(
        filename=log_dir / "flask_debug.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_debug_handler.setLevel(logging.DEBUG)
    file_debug_handler.setFormatter(detailed_formatter)

    file_error_handler = RotatingFileHandler(
        filename=log_dir / "flask_error.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_error_handler.setLevel(logging.WARNING)
    file_error_handler.setFormatter(detailed_formatter)

    # Настройка основного логгера приложения
    app.logger.setLevel(logging.DEBUG)

    # Удаляем все существующие обработчики
    for handler in list(app.logger.handlers):
        app.logger.removeHandler(handler)

    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_debug_handler)
    app.logger.addHandler(file_error_handler)

    # Настройка логгеров для зависимостей
    dependency_loggers = {
        'sqlite3': logging.WARNING,
        'apscheduler': logging.INFO,
        'werkzeug': logging.INFO if app.debug else logging.WARNING,
        'googleapiclient': logging.WARNING,
        'flask_login': logging.INFO,
        'oauthlib': logging.WARNING,
        'requests_oauthlib': logging.WARNING
    }

    for logger_name, level in dependency_loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        # Удаляем все обработчики для этого логгера
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
        # Добавляем нужные обработчики
        if level <= logging.INFO:
            logger.addHandler(console_handler)
        logger.addHandler(file_error_handler)
        logger.propagate = False

    # Для режима разработки можно включить более подробное логирование Werkzeug
    if app.debug:
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.DEBUG)
        werkzeug_logger.addHandler(console_handler)