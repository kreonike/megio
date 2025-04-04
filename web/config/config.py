# config/config.py
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from flask import g

# Загрузка переменных окружения из .env файла
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent  # Поднимаемся на уровень выше до web/
DB_DIR = os.path.join(BASE_DIR, '..', 'database')  # Добавляем переход на уровень выше для доступа к project/database
DB_PATH = os.path.join(DB_DIR, 'tasks.db')  # Или 'tasks.py', если это действительно файл Python
DB_TIMEOUT = 30

# Настройки приложения
SECRET_KEY = os.getenv('SECRET_KEY')

# Настройки Google OAuth
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Русские названия месяцев
MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=30)
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# config/config.py (добавьте в конец файла)
def init_db(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            telegram_token TEXT UNIQUE,
            google_token TEXT
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            task TEXT NOT NULL,
            time TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            repeat_days INTEGER DEFAULT NULL,
            repeat_start TEXT DEFAULT NULL,
            repeat_end TEXT DEFAULT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_users (
            telegram_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')
        db.commit()

        cursor.execute('PRAGMA table_info(tasks)')
        columns = [row[1] for row in cursor.fetchall()]

        if 'repeat_days' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN repeat_days INTEGER DEFAULT NULL')
        if 'repeat_start' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN repeat_start TEXT DEFAULT NULL')
        if 'repeat_end' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN repeat_end TEXT DEFAULT NULL')
        db.commit()