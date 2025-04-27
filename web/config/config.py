import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = os.path.join(BASE_DIR, '..', 'database')
DB_PATH = os.path.join(DB_DIR, 'tasks.db')
DB_TIMEOUT = 30

SECRET_KEY = os.getenv('SECRET_KEY')

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

@contextmanager
def db_connection():
    db = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    db.execute('PRAGMA journal_mode=WAL')
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

def init_db(app):
    with app.app_context():
        with db_connection() as db:
            cursor = db.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                telegram_token TEXT UNIQUE,
                google_token TEXT,
                timezone TEXT DEFAULT 'UTC'
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
                priority INTEGER DEFAULT 1,
                reminder_15m_sent INTEGER DEFAULT 0,
                reminder_2h_sent INTEGER DEFAULT 0,
                reminder_1day_sent INTEGER DEFAULT 0,
                google_event_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT '#3498db',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_categories (
                task_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                PRIMARY KEY (task_id, category_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS telegram_users (
                telegram_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS completed_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                task_text TEXT NOT NULL,
                completion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                priority INTEGER DEFAULT 1,
                categories TEXT,
                original_year INTEGER,
                original_month INTEGER,
                original_day INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''')

            # Добавление индекса для google_event_id
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tasks_google_event_id ON tasks(google_event_id)
            ''')

            db.commit()

            # Проверка и добавление отсутствующих столбцов
            cursor.execute('PRAGMA table_info(users)')
            user_columns = [row[1] for row in cursor.fetchall()]
            if 'timezone' not in user_columns:
                cursor.execute('ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT "UTC"')

            cursor.execute('PRAGMA table_info(tasks)')
            columns = [row[1] for row in cursor.fetchall()]
            if 'priority' not in columns:
                cursor.execute('ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 1')
            if 'reminder_15m_sent' not in columns:
                cursor.execute('ALTER TABLE tasks ADD COLUMN reminder_15m_sent INTEGER DEFAULT 0')
            if 'reminder_2h_sent' not in columns:
                cursor.execute('ALTER TABLE tasks ADD COLUMN reminder_2h_sent INTEGER DEFAULT 0')
            if 'reminder_1day_sent' not in columns:
                cursor.execute('ALTER TABLE tasks ADD COLUMN reminder_1day_sent INTEGER DEFAULT 0')
            if 'google_event_id' not in columns:
                cursor.execute('ALTER TABLE tasks ADD COLUMN google_event_id TEXT')

            cursor.execute('PRAGMA table_info(completed_tasks)')
            completed_columns = [row[1] for row in cursor.fetchall()]
            if 'original_year' not in completed_columns:
                cursor.execute('ALTER TABLE completed_tasks ADD COLUMN original_year INTEGER')
            if 'original_month' not in completed_columns:
                cursor.execute('ALTER TABLE completed_tasks ADD COLUMN original_month INTEGER')
            if 'original_day' not in completed_columns:
                cursor.execute('ALTER TABLE completed_tasks ADD COLUMN original_day INTEGER')

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='categories'")
            if not cursor.fetchone():
                cursor.execute('''
                CREATE TABLE categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    color TEXT NOT NULL DEFAULT '#3498db',
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )''')

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

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='completed_tasks'")
            if not cursor.fetchone():
                cursor.execute('''
                CREATE TABLE completed_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    task_id INTEGER NOT NULL,
                    task_text TEXT NOT NULL,
                    completion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    priority INTEGER DEFAULT 1,
                    categories TEXT,
                    original_year INTEGER,
                    original_month INTEGER,
                    original_day INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )''')
            else:
                cursor.execute('PRAGMA table_info(completed_tasks)')
                completed_tasks_columns = [row[1] for row in cursor.fetchall()]
                if 'categories' not in completed_tasks_columns:
                    cursor.execute('ALTER TABLE completed_tasks ADD COLUMN categories TEXT')
                if 'original_year' not in completed_tasks_columns:
                    cursor.execute('ALTER TABLE completed_tasks ADD COLUMN original_year INTEGER')
                if 'original_month' not in completed_tasks_columns:
                    cursor.execute('ALTER TABLE completed_tasks ADD COLUMN original_month INTEGER')
                if 'original_day' not in completed_tasks_columns:
                    cursor.execute('ALTER TABLE completed_tasks ADD COLUMN original_day INTEGER')

            db.commit()