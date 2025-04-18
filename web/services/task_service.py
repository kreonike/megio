# web/services/task_service.py
from datetime import datetime
import json


class PermissionError(Exception):
    pass


def check_ownership(cursor, table, id, user_id):
    """
    Проверяет, принадлежит ли запись в указанной таблице пользователю.
    """
    cursor.execute(f'SELECT user_id FROM {table} WHERE id = ?', (id,))
    record = cursor.fetchone()
    if not record or record['user_id'] != user_id:
        raise PermissionError(f"No access to {table} with id {id}")


def update_task_categories(db, task_id, category_ids):
    """
    Обновляет связи задачи с категориями в таблице task_categories.
    """
    cursor = db.cursor()
    cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
    if category_ids:
        for cat_id in category_ids:
            cursor.execute('INSERT INTO task_categories (task_id, category_id) VALUES (?, ?)', (task_id, cat_id))
    db.commit()


def get_task_categories(db, task_id):
    """
    Получает список категорий для задачи.
    """
    cursor = db.cursor()
    cursor.execute('''
        SELECT group_concat(c.name, ', ') as categories
        FROM task_categories tc
        JOIN categories c ON tc.category_id = c.id
        WHERE tc.task_id = ?
    ''', (task_id,))
    result = cursor.fetchone()
    return result['categories'] if result and result['categories'] else ''


def complete_task(db, user_id, task_id, year, month, day):
    """Завершает задачу, перемещая ее в completed_tasks."""
    cursor = db.cursor()

    check_ownership(cursor, 'tasks', task_id, user_id)

    # Получаем категории задачи
    categories = get_task_categories(db, task_id)

    cursor.execute('''
        SELECT id, task, priority
        FROM tasks
        WHERE id = ? AND user_id = ?
    ''', (task_id, user_id))
    task = cursor.fetchone()

    if not task:
        raise PermissionError("Task not found")

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
        categories,  # Используем полученные категории
        year,
        month,
        day,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))
    completed_id = cursor.lastrowid

    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()

    return completed_id


def restore_task(db, user_id, completed_task_id, year, month, day):
    """Восстанавливает задачу из completed_tasks в tasks."""
    cursor = db.cursor()

    check_ownership(cursor, 'completed_tasks', completed_task_id, user_id)

    cursor.execute('''
        SELECT id, task_id, task_text, priority, categories
        FROM completed_tasks
        WHERE id = ? AND user_id = ?
    ''', (completed_task_id, user_id))
    completed_task = cursor.fetchone()

    if not completed_task:
        raise PermissionError("Completed task not found")

    # Вставляем задачу без колонки categories
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

    # Если есть категории, восстанавливаем их через task_categories
    if completed_task['categories']:
        # Здесь можно добавить логику для восстановления категорий,
        # если это необходимо в вашем приложении
        pass

    cursor.execute('DELETE FROM completed_tasks WHERE id = ?', (completed_task_id,))
    db.commit()

    return new_task_id


def add_task(db, user_id, year, month, day, task_text, time=None, priority=1, category_ids=None, repeat_days=None,
             repeat_start=None, repeat_end=None):
    cursor = db.cursor()
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
    update_task_categories(db, task_id, category_ids)
    return task_id


def edit_task(db, user_id, task_id, task_text, time=None, priority=1, category_ids=None, repeat_days=None,
              repeat_start=None, repeat_end=None):
    cursor = db.cursor()
    check_ownership(cursor, 'tasks', task_id, user_id)
    cursor.execute('''
        UPDATE tasks 
        SET task = ?, time = ?, priority = ?, repeat_days = ?, repeat_start = ?, repeat_end = ?
        WHERE id = ?
    ''', (task_text, time, priority, repeat_days, repeat_start, repeat_end, task_id))
    update_task_categories(db, task_id, category_ids)


def delete_task(db, user_id, task_id):
    cursor = db.cursor()
    check_ownership(cursor, 'tasks', task_id, user_id)
    cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()