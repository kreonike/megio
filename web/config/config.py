# web/config.py
import os
from pathlib import Path
import secrets
import sqlite3
from flask import g

# Константы приложения
MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

# Конфигурация Google OAuth
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')

# Настройки приложения
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
OAUTHLIB_INSECURE_TRANSPORT = os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '1')  # Только для разработки!

# Настройки базы данных
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Путь к базе данных
DB_PATH = BASE_DIR / "database" / "tasks.db"
DB_TIMEOUT = 30

# Настройки планировщика
SYNC_INTERVAL_MINUTES = 2
GOOGLE_EVENTS_MAX_RESULTS = 10

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()