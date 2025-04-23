import sqlite3
import os
from pathlib import Path


def migrate_database(db_path):
    print(f"Попытка подключения к базе данных: {db_path}")

    # Проверяем, существует ли файл
    if not os.path.exists(db_path):
        print(f"Ошибка: файл базы данных не найден по пути {db_path}")
        return False

    # Проверяем права доступа
    if not os.access(db_path, os.R_OK | os.W_OK):
        print(f"Ошибка: нет прав на чтение/запись для файла {db_path}")
        return False

    conn = None
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Проверяем наличие таблицы completed_tasks
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='completed_tasks'")
        if not cursor.fetchone():
            print("Создаём таблицу completed_tasks...")
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
                )
            ''')
            print("Таблица completed_tasks создана.")
        else:
            print("Таблица completed_tasks уже существует.")

        # Проверяем столбцы в completed_tasks
        cursor.execute('PRAGMA table_info(completed_tasks)')
        columns = [col['name'] for col in cursor.fetchall()]
        print("Текущие столбцы в таблице completed_tasks:", columns)

        # Добавляем недостающие столбцы
        for col, col_type in [
            ('categories', 'TEXT'),
            ('original_year', 'INTEGER'),
            ('original_month', 'INTEGER'),
            ('original_day', 'INTEGER')
        ]:
            if col not in columns:
                print(f"Добавляем столбец {col}...")
                cursor.execute(f"ALTER TABLE completed_tasks ADD COLUMN {col} {col_type}")
                print(f"Столбец {col} успешно добавлен.")
            else:
                print(f"Столбец {col} уже существует.")

        # Проверяем столбцы в tasks (для reminder_15m_sent и др.)
        cursor.execute('PRAGMA table_info(tasks)')
        task_columns = [col['name'] for col in cursor.fetchall()]
        print("Текущие столбцы в таблице tasks:", task_columns)

        for col in ['reminder_15m_sent', 'reminder_2h_sent', 'reminder_1day_sent']:
            if col not in task_columns:
                print(f"Добавляем столбец {col}...")
                cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col} INTEGER DEFAULT 0")
                print(f"Столбец {col} успешно добавлен.")
            else:
                print(f"Столбец {col} уже существует.")

        if 'google_event_id' not in task_columns:
            print("Добавляем столбец google_event_id...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN google_event_id TEXT")
            print("Столбец google_event_id успешно добавлен.")
        else:
            print("Столбец google_event_id уже существует.")

        # Подтверждаем изменения
        conn.commit()
        print("Миграция успешно завершена.")
        return True

    except sqlite3.Error as e:
        print(f"Ошибка при миграции базы данных: {e}")
        return False
    finally:
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто.")


if __name__ == "__main__":
    # Используем тот же путь, что в config.py
    BASE_DIR = Path(__file__).resolve().parent.parent
    DB_DIR = os.path.join(BASE_DIR, '..', 'database')
    DB_PATH = os.path.join(DB_DIR, 'tasks.db')
    migrate_database(DB_PATH)