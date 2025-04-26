# web/services/task_service.py
from datetime import datetime, timedelta
import json
from flask import current_app as app


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
        raise PermissionError(f"Нет доступа к {table} с id {id}")


def complete_task(db, user_id, task_id, year, month, day):
    """
    Завершает задачу, перемещая её в таблицу завершённых задач и удаляя из активных.

    Args:
        db: Соединение с базой данных.
        user_id: ID пользователя.
        task_id: ID задачи.
        year, month, day: Дата задачи.

    Returns:
        ID завершённой задачи.
    """
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
        raise PermissionError("Задача не найдена")

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
    """
    Восстанавливает завершённую задачу в активные задачи.

    Args:
        db: Соединение с базой данных.
        user_id: ID пользователя.
        completed_task_id: ID завершённой задачи.
        year, month, day: Дата восстановления.

    Returns:
        ID восстановленной задачи.
    """
    cursor = db.cursor()
    check_ownership(cursor, 'completed_tasks', completed_task_id, user_id)

    cursor.execute('''
        SELECT task_id, task_text, priority, categories
        FROM completed_tasks
        WHERE id = ? AND user_id = ?
    ''', (completed_task_id, user_id))
    completed_task = cursor.fetchone()

    if not completed_task:
        raise PermissionError("Завершённая задача не найдена")

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
    """
    Добавляет новую задачу в базу данных. Сохраняет только основную задачу, повторяющиеся экземпляры обрабатываются динамически.

    Args:
        db: Соединение с базой данных.
        user_id: ID пользователя.
        year, month, day: Дата задачи.
        task_text: Текст задачи.
        time: Время задачи (опционально).
        priority: Приоритет (1=низкий, 2=средний, 3=высокий).
        category_ids: Список ID категорий.
        repeat_days: Количество дней для повторения (опционально).
        repeat_start: Дата начала повторения (опционально).
        repeat_end: Дата окончания повторения (опционально).

    Returns:
        ID созданной задачи.
    """
    cursor = db.cursor()

    # Проверяем параметры повторения
    if repeat_days or repeat_start or repeat_end:
        if not (repeat_days and repeat_start and repeat_end):
            app.logger.warning(f"Некорректные параметры повторения для задачи: repeat_days={repeat_days}, repeat_start={repeat_start}, repeat_end={repeat_end}")
            repeat_days = None
            repeat_start = None
            repeat_end = None
        else:
            try:
                start_date = datetime.strptime(repeat_start, '%Y-%m-%d')
                end_date = datetime.strptime(repeat_end, '%Y-%m-%d')
                if start_date > end_date or repeat_days <= 0:
                    app.logger.warning(f"Некорректные параметры повторения для задачи: start_date={repeat_start}, end_date={repeat_end}, repeat_days={repeat_days}")
                    repeat_days = None
                    repeat_start = None
                    repeat_end = None
            except ValueError as e:
                app.logger.error(f"Некорректный формат даты для повторения задачи: {e}")
                repeat_days = None
                repeat_start = None
                repeat_end = None

    # Создаём начальную задачу
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

    db.commit()
    app.logger.debug(f"Создана задача {task_id} для {year}-{month}-{day}, repeat_days={repeat_days}, repeat_start={repeat_start}, repeat_end={repeat_end}")
    return task_id


def edit_task(db, user_id, task_id, task_text, time=None, priority=1, category_ids=None, repeat_days=None,
              repeat_start=None, repeat_end=None):
    """
    Редактирует существующую задачу. Обновляет только основную задачу.

    Args:
        db: Соединение с базой данных.
        user_id: ID пользователя.
        task_id: ID задачи.
        task_text: Новый текст задачи.
        time: Новое время задачи (опционально).
        priority: Новый приоритет.
        category_ids: Новый список ID категорий.
        repeat_days: Новое количество дней для повторения (опционально).
        repeat_start: Новая дата начала повторения (опционально).
        repeat_end: Новая дата окончания повторения (опционально).
    """
    cursor = db.cursor()
    check_ownership(cursor, 'tasks', task_id, user_id)

    # Проверяем параметры повторения
    if repeat_days or repeat_start or repeat_end:
        if not (repeat_days and repeat_start and repeat_end):
            app.logger.warning(f"Некорректные параметры повторения для задачи {task_id}: repeat_days={repeat_days}, repeat_start={repeat_start}, repeat_end={repeat_end}")
            repeat_days = None
            repeat_start = None
            repeat_end = None
        else:
            try:
                start_date = datetime.strptime(repeat_start, '%Y-%m-%d')
                end_date = datetime.strptime(repeat_end, '%Y-%m-%d')
                if start_date > end_date or repeat_days <= 0:
                    app.logger.warning(f"Некорректные параметры повторения для задачи {task_id}: start_date={repeat_start}, end_date={repeat_end}, repeat_days={repeat_days}")
                    repeat_days = None
                    repeat_start = None
                    repeat_end = None
            except ValueError as e:
                app.logger.error(f"Некорректный формат даты для повторения задачи {task_id}: {e}")
                repeat_days = None
                repeat_start = None
                repeat_end = None

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

    db.commit()
    app.logger.debug(f"Обновлена задача {task_id} для repeat_days={repeat_days}, repeat_start={repeat_start}, repeat_end={repeat_end}")


def delete_task(db, user_id, task_id):
    """
    Удаляет задачу и связанные категории.

    Args:
        db: Соединение с базой данных.
        user_id: ID пользователя.
        task_id: ID задачи.
    """
    cursor = db.cursor()
    check_ownership(cursor, 'tasks', task_id, user_id)

    # Удаляем текущую задачу
    cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

    db.commit()