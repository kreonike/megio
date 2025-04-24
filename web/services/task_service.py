# web/services/task_service.py
from datetime import datetime, timedelta
import json


class PermissionError(Exception):
    pass


def check_ownership(cursor, table, id, user_id):
    """
    Проверяет, принадлежит ли запись в указанной таблице пользователю.

    Args:
        cursor: Курсор базы данных.
        table (str): Название таблицы.
        id: ID записи.
        user_id: ID пользователя.

    Raises:
        PermissionError: Если запись не найдена или принадлежит другому пользователю.
    """
    cursor.execute(f'SELECT user_id FROM {table} WHERE id = ?', (id,))
    record = cursor.fetchone()
    if not record or record['user_id'] != user_id:
        raise PermissionError(f"No access to {table} with id {id}")


def complete_task(db, user_id, task_id, year, month, day):
    cursor = db.cursor()
    check_ownership(cursor, 'tasks', task_id, user_id)

    # Получаем данные задачи и категории
    cursor.execute('''
        SELECT t.id, t.task, t.priority
        FROM tasks t
        WHERE t.id = ? AND t.user_id = ?
    ''', (task_id, user_id))
    task = cursor.fetchone()

    if not task:
        raise PermissionError("Task not found")

    # Получаем категории задачи
    cursor.execute('''
        SELECT GROUP_CONCAT(category_id) AS categories
        FROM task_categories
        WHERE task_id = ?
    ''', (task_id,))
    categories_row = cursor.fetchone()
    categories = categories_row['categories'] if categories_row and categories_row['categories'] else None

    # Записываем задачу в completed_tasks
    cursor.execute('''
        INSERT INTO completed_tasks (
            user_id, task_id, task_text, priority, categories,
            original_year, original_month, original_day, completion_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        task_id,
        task['task'],
        task['priority'],
        categories,
        year,
        month,
        day,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    completed_id = cursor.lastrowid

    # Удаляем задачу из tasks
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
    db.commit()

    return completed_id


def restore_task(db, user_id, completed_task_id, year, month, day):
    cursor = db.cursor()
    check_ownership(cursor, 'completed_tasks', completed_task_id, user_id)

    cursor.execute('''
        SELECT task_id, task_text, priority, categories
        FROM completed_tasks
        WHERE id = ? AND user_id = ?
    ''', (completed_task_id, user_id))
    completed_task = cursor.fetchone()

    if not completed_task:
        raise PermissionError("Completed task not found")

    # Восстанавливаем задачу в tasks
    cursor.execute('''
        INSERT INTO tasks (user_id, task, year, month, day, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        completed_task['task_text'],
        year,
        month,
        day,
        completed_task['priority']
    ))
    new_task_id = cursor.lastrowid

    # Восстанавливаем категории, если они есть
    if completed_task['categories']:
        for cat_id in completed_task['categories'].split(','):
            cursor.execute('''
                INSERT INTO task_categories (task_id, category_id)
                VALUES (?, ?)
            ''', (new_task_id, int(cat_id)))

    cursor.execute('DELETE FROM completed_tasks WHERE id = ?', (completed_task_id,))
    db.commit()

    return new_task_id


def add_task(db, user_id, year, month, day, task_text, time=None, priority=1, category_ids=None, repeat_days=None,
             repeat_start=None, repeat_end=None):
    cursor = db.cursor()

    # Создаем начальную задачу
    cursor.execute('''
        INSERT INTO tasks (user_id, year, month, day, task, time, priority, repeat_days, repeat_start, repeat_end, created)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        year,
        month,
        day,
        task_text,
        time,
        priority,
        repeat_days,
        repeat_start,
        repeat_end,
        datetime.now()
    ))
    task_id = cursor.lastrowid

    # Сохраняем категории
    if category_ids:
        for cat_id in category_ids:
            cursor.execute('INSERT INTO task_categories (task_id, category_id) VALUES (?, ?)', (task_id, cat_id))

    # Создаем повторяющиеся задачи, если указаны параметры
    if repeat_days and repeat_start and repeat_end and repeat_days > 0:
        try:
            start_date = datetime.strptime(repeat_start, '%Y-%m-%d')
            end_date = datetime.strptime(repeat_end, '%Y-%m-%d')
            current_date = start_date + timedelta(days=repeat_days)

            while current_date <= end_date:
                cursor.execute('''
                    INSERT INTO tasks (user_id, year, month, day, task, time, priority, repeat_days, repeat_start, repeat_end, created)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    current_date.year,
                    current_date.month,
                    current_date.day,
                    task_text,
                    time,
                    priority,
                    repeat_days,
                    repeat_start,
                    repeat_end,
                    datetime.now()
                ))
                new_task_id = cursor.lastrowid
                if category_ids:
                    for cat_id in category_ids:
                        cursor.execute('INSERT INTO task_categories (task_id, category_id) VALUES (?, ?)',
                                       (new_task_id, cat_id))

                current_date += timedelta(days=repeat_days)
        except ValueError as e:
            db.rollback()
            raise ValueError(f"Ошибка в формате дат повторения: {e}")

    db.commit()
    return task_id


def edit_task(db, user_id, task_id, task_text, time=None, priority=1, category_ids=None, repeat_days=None,
              repeat_start=None, repeat_end=None):
    cursor = db.cursor()
    check_ownership(cursor, 'tasks', task_id, user_id)

    # Получаем данные текущей задачи
    cursor.execute('SELECT repeat_start FROM tasks WHERE id = ?', (task_id,))
    original_task = cursor.fetchone()
    original_repeat_start = original_task['repeat_start'] if original_task else None

    # Удаляем все связанные повторяющиеся задачи (если были)
    if original_repeat_start:
        cursor.execute('''
            DELETE FROM tasks
            WHERE user_id = ? AND repeat_start = ? AND id != ?
        ''', (user_id, original_repeat_start, task_id))
        cursor.execute('''
            DELETE FROM task_categories
            WHERE task_id IN (
                SELECT id FROM tasks
                WHERE user_id = ? AND repeat_start = ? AND id != ?
            )
        ''', (user_id, original_repeat_start, task_id))

    # Обновляем текущую задачу
    cursor.execute('''
        UPDATE tasks 
        SET task = ?, time = ?, priority = ?, repeat_days = ?, repeat_start = ?, repeat_end = ?
        WHERE id = ?
    ''', (task_text, time, priority, repeat_days, repeat_start, repeat_end, task_id))

    # Обновляем категории
    cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
    if category_ids:
        for cat_id in category_ids:
            cursor.execute('INSERT INTO task_categories (task_id, category_id) VALUES (?, ?)', (task_id, cat_id))

    # Создаем новые повторяющиеся задачи
    if repeat_days and repeat_start and repeat_end and repeat_days > 0:
        try:
            start_date = datetime.strptime(repeat_start, '%Y-%m-%d')
            end_date = datetime.strptime(repeat_end, '%Y-%m-%d')
            current_date = start_date + timedelta(days=repeat_days)

            while current_date <= end_date:
                cursor.execute('''
                    INSERT INTO tasks (user_id, year, month, day, task, time, priority, repeat_days, repeat_start, repeat_end, created)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    current_date.year,
                    current_date.month,
                    current_date.day,
                    task_text,
                    time,
                    priority,
                    repeat_days,
                    repeat_start,
                    repeat_end,
                    datetime.now()
                ))
                new_task_id = cursor.lastrowid
                if category_ids:
                    for cat_id in category_ids:
                        cursor.execute('INSERT INTO task_categories (task_id, category_id) VALUES (?, ?)',
                                       (new_task_id, cat_id))

                current_date += timedelta(days=repeat_days)
        except ValueError as e:
            db.rollback()
            raise ValueError(f"Ошибка в формате дат повторения: {e}")

    db.commit()


def delete_task(db, user_id, task_id):
    cursor = db.cursor()
    check_ownership(cursor, 'tasks', task_id, user_id)

    # Получаем repeat_start для удаления связанных задач
    cursor.execute('SELECT repeat_start FROM tasks WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    repeat_start = task['repeat_start'] if task else None

    # Удаляем текущую задачу
    cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

    # Удаляем связанные повторяющиеся задачи
    if repeat_start:
        cursor.execute('''
            DELETE FROM tasks
            WHERE user_id = ? AND repeat_start = ?
        ''', (user_id, repeat_start))
        cursor.execute('''
            DELETE FROM task_categories
            WHERE task_id IN (
                SELECT id FROM tasks
                WHERE user_id = ? AND repeat_start = ?
            )
        ''', (user_id, repeat_start))

    db.commit()