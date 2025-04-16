# web/services/category_service.py
def get_user_categories(db, user_id):
    cursor = db.cursor()
    cursor.execute('SELECT id, name, color FROM categories WHERE user_id = ?', (user_id,))
    return [dict(row) for row in cursor.fetchall()]


def parse_category_ids(category_ids_str):
    """
    Парсит строку идентификаторов категорий в список целых чисел.

    Args:
        category_ids_str (str): Строка с идентификаторами, разделенными запятыми.

    Returns:
        list: Список целых чисел (ID категорий).
    """
    return [int(cid) for cid in category_ids_str.split(',')] if category_ids_str else []


def get_default_categories(db, user_id):
    """
    Получает или создает категории по умолчанию ('Личное', 'Работа') для пользователя.

    Args:
        db: Соединение с базой данных.
        user_id: ID пользователя.

    Returns:
        list: Список словарей с категориями.
    """
    cursor = db.cursor()

    # Проверяем, есть ли категории у пользователя
    cursor.execute('SELECT id, name, color FROM categories WHERE user_id = ?', (user_id,))
    categories = [dict(row) for row in cursor.fetchall()]

    # Если категорий нет, создаем категории по умолчанию
    if not categories:
        default_categories = [
            {'name': 'Личное', 'color': '#4CAF50'},
            {'name': 'Работа', 'color': '#2196F3'}
        ]
        for cat in default_categories:
            cursor.execute(
                'INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)',
                (user_id, cat['name'], cat['color'])
            )
        db.commit()
        # Повторно запрашиваем категории
        cursor.execute('SELECT id, name, color FROM categories WHERE user_id = ?', (user_id,))
        categories = [dict(row) for row in cursor.fetchall()]

    return categories