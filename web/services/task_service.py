from datetime import datetime


class PermissionError(Exception):
    pass


class GoogleCalendarError(Exception):
    pass


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
    if category_ids:
        for cat_id in category_ids:
            cursor.execute('INSERT INTO task_categories (task_id, category_id) VALUES (?, ?)', (task_id, cat_id))
    db.commit()
    return task_id


def edit_task(db, user_id, task_id, task_text, time=None, priority=1, category_ids=None, repeat_days=None,
              repeat_start=None, repeat_end=None):
    cursor = db.cursor()
    cursor.execute('SELECT user_id FROM tasks WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    if not task or task['user_id'] != user_id:
        raise PermissionError("No access to task")
    cursor.execute('''
        UPDATE tasks 
        SET task = ?, time = ?, priority = ?, repeat_days = ?, repeat_start = ?, repeat_end = ?
        WHERE id = ?
    ''', (task_text, time, priority, repeat_days, repeat_start, repeat_end, task_id))
    cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
    if category_ids:
        for cat_id in category_ids:
            cursor.execute('INSERT INTO task_categories (task_id, category_id) VALUES (?, ?)', (task_id, cat_id))
    db.commit()


def delete_task(db, user_id, task_id):
    cursor = db.cursor()
    cursor.execute('SELECT user_id, google_event_id FROM tasks WHERE id = ?', (task_id,))
    task = cursor.fetchone()
    if not task or task['user_id'] != user_id:
        raise PermissionError("No access to task")
    if task['google_event_id']:
        raise GoogleCalendarError("Cannot delete Google Calendar task")
    cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()


def complete_task(db, user_id, task_id, year, month, day):
    cursor = db.cursor()

    # Получаем данные задачи
    cursor.execute('''
        SELECT t.id, t.task, t.priority, 
               GROUP_CONCAT(c.name) as categories
        FROM tasks t
        LEFT JOIN task_categories tc ON t.id = tc.task_id
        LEFT JOIN categories c ON tc.category_id = c.id
        WHERE t.id = ? AND t.user_id = ?
        GROUP BY t.id
    ''', (task_id, user_id))

    task = cursor.fetchone()
    if not task:
        raise PermissionError("Task not found")

    # Сохраняем в completed_tasks
    cursor.execute('''
        INSERT INTO completed_tasks
        (user_id, task_id, task_text, priority, categories, 
         original_year, original_month, original_day)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        task['id'],
        task['task'],
        task['priority'],
        task['categories'],
        year,
        month,
        day
    ))
    completed_id = cursor.lastrowid

    # Удаляем оригинальную задачу
    cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()

    return completed_id  # Возвращаем ID в completed_tasks


def restore_task(db, user_id, completed_task_id, year, month, day):
    cursor = db.cursor()

    # 1. Получаем полные данные задачи
    cursor.execute('''
        SELECT task_id, task_text, priority, categories
        FROM completed_tasks
        WHERE id = ? AND user_id = ?
    ''', (completed_task_id, user_id))

    task = cursor.fetchone()
    if not task:
        raise ValueError(f"Задача {completed_task_id} не найдена")

    # 2. Создаем новую задачу
    cursor.execute('''
        INSERT INTO tasks (user_id, year, month, day, task, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        year,
        month,
        day,
        task['task_text'],
        task['priority']
    ))
    new_task_id = cursor.lastrowid

    # 3. Восстанавливаем категории
    if task['categories']:
        categories = [c.strip() for c in task['categories'].split(',') if c.strip()]
        for category in categories:
            cursor.execute('''
                SELECT id FROM categories 
                WHERE user_id = ? AND name = ?
            ''', (user_id, category))
            cat = cursor.fetchone()
            if cat:
                cursor.execute('''
                    INSERT INTO task_categories (task_id, category_id)
                    VALUES (?, ?)
                ''', (new_task_id, cat['id']))

    # 4. Удаляем из выполненных задач
    cursor.execute('DELETE FROM completed_tasks WHERE id = ?', (completed_task_id,))
    db.commit()

    return new_task_id