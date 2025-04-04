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


def init_db(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            telegram_token TEXT UNIQUE,
            google_token TEXT
        )''')

        # Таблица задач
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
            priority INTEGER DEFAULT 1,  -- 1-низкий, 2-средний, 3-высокий
            reminder_15m_sent INTEGER DEFAULT 0,
            reminder_2h_sent INTEGER DEFAULT 0,
            reminder_1day_sent INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')

        # Таблица категорий
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT '#3498db',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

        # Таблица связи задач с категориями
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_categories (
            task_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            PRIMARY KEY (task_id, category_id),
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )''')

        # Таблица Telegram пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_users (
            telegram_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')

        db.commit()

        # Проверка и добавление отсутствующих столбцов
        cursor.execute('PRAGMA table_info(tasks)')
        columns = [row[1] for row in cursor.fetchall()]

        # Добавление новых столбцов, если они отсутствуют
        if 'priority' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 1')

        if 'reminder_15m_sent' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN reminder_15m_sent INTEGER DEFAULT 0')

        if 'reminder_2h_sent' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN reminder_2h_sent INTEGER DEFAULT 0')

        if 'reminder_1day_sent' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN reminder_1day_sent INTEGER DEFAULT 0')

        # Проверка существования таблицы категорий
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
        if not cursor.fetchone():
            cursor.execute('''
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT '#3498db',
                FOREIGN KEY (user_id) REFERENCES users(id)
            ''')

        # Проверка существования таблицы task_categories
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_categories'")
        if not cursor.fetchone():
            cursor.execute('''
            CREATE TABLE task_categories (
                task_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                PRIMARY KEY (task_id, category_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )''')

        db.commit()