# web/services/category_service.py
from web.config.config import db_connection
from web.utils import log_action


def get_user_categories(db, user_id):
    """
    Получает список категорий пользователя.

    Args:
        db: Соединение с базой данных.
        user_id: ID пользователя.

    Returns:
        Список словарей с полями id, name, color.
    """
    cursor = db.cursor()
    cursor.execute('SELECT id, name, color FROM categories WHERE user_id = ?', (user_id,))
    return [dict(row) for row in cursor.fetchall()]


def add_category(db, user_id, name, color, logger=None):
    """
    Добавляет новую категорию для пользователя.

    Args:
        db: Соединение с базой данных.
        user_id: ID пользователя.
        name: Название категории.
        color: Цвет категории (в формате HEX).
        logger: Логгер для записи действия (опционально).

    Returns:
        ID созданной категории.
    """
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO categories (user_id, name, color) 
        VALUES (?, ?, ?)
    ''', (user_id, name, color))
    category_id = cursor.lastrowid
    db.commit()
    if logger:
        log_action(logger, "Category", "added", user_id, name=name)
    return category_id


def delete_category(db, user_id, category_id, logger=None):
    """
    Удаляет категорию пользователя и связанные с ней связи с задачами.

    Args:
        db: Соединение с базой данных.
        user_id: ID пользователя.
        category_id: ID категории.
        logger: Логгер для записи действия (опционально).

    Returns:
        Количество удалённых строк (0 или 1).
    """
    cursor = db.cursor()
    # Удаляем связи с задачами
    cursor.execute('''
        DELETE FROM task_categories 
        WHERE category_id = ? AND task_id IN (
            SELECT id FROM tasks WHERE user_id = ?
        )
    ''', (category_id, user_id))
    # Удаляем саму категорию
    cursor.execute('DELETE FROM categories WHERE id = ? AND user_id = ?', (category_id, user_id))
    affected = cursor.rowcount
    db.commit()
    if affected and logger:
        log_action(logger, "Category", "deleted", user_id, entity_id=category_id)
    return affected