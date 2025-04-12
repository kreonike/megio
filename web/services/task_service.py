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
    cursor.execute('SELECT id, user_id, task, priority FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
    task = cursor.fetchone()
    if not task:
        raise PermissionError("Task not found")

    cursor.execute('''
        SELECT c.name
        FROM categories c
        JOIN task_categories tc ON c.id = tc.category_id
        WHERE tc.task_id = ?
    ''', (task_id,))
    categories = [row['name'] for row in cursor.fetchall()]

    cursor.execute('''
        INSERT INTO completed_tasks
        (user_id, task_id, task_text, priority, categories, original_year, original_month, original_day)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        task_id,
        task['task'],
        task['priority'],
        ','.join(categories) if categories else None,
        year,
        month,
        day
    ))

    cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()


def restore_task(db, user_id, completed_task_id, year, month, day):
    cursor = db.cursor()
    cursor.execute('''
        SELECT task_id, task_text, priority, categories, original_year, original_month, original_day
        FROM completed_tasks
        WHERE id = ? AND user_id = ?
    ''', (completed_task_id, user_id))
    completed_task = cursor.fetchone()

    if not completed_task:
        raise PermissionError("Completed task not found")

    cursor.execute('''
        INSERT INTO tasks (id, user_id, year, month, day, task, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        completed_task['task_id'],
        user_id,
        year,
        month,
        day,
        completed_task['task_text'],
        completed_task['priority']
    ))

    if completed_task['categories']:
        category_names = completed_task['categories'].split(',')
        for category_name in category_names:
            cursor.execute('''
                SELECT id FROM categories WHERE user_id = ? AND name = ?
            ''', (user_id, category_name.strip()))
            category = cursor.fetchone()
            if category:
                cursor.execute('''
                    INSERT OR IGNORE INTO task_categories (task_id, category_id)
                    VALUES (?, ?)
                ''', (completed_task['task_id'], category['id']))

    cursor.execute('DELETE FROM completed_tasks WHERE id = ?', (completed_task_id,))
    db.commit()