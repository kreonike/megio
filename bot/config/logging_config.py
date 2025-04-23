import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Путь к логам относительно корня проекта
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "bot/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

dict_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "base": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "base",
            "stream": "ext://sys.stdout"
        },
        "file_debug": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOG_DIR / "bot_debug.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "encoding": "utf-8"
        },
        "file_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "WARNING",
            "formatter": "detailed",
            "filename": LOG_DIR / "bot_error.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "encoding": "utf-8"
        }
    },
    "loggers": {
        "bot": {
            "level": "DEBUG",
            "handlers": ["console", "file_debug", "file_error"],
            "propagate": False
        },
        "aiogram": {
            "level": "INFO",
            "handlers": ["console", "file_error"],
            "propagate": False
        },
        "sqlite3": {
            "level": "WARNING",
            "handlers": ["file_error"],
            "propagate": False
        }
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console"]
    }
}