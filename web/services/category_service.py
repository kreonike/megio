def get_user_categories(db, user_id):
    cursor = db.cursor()
    cursor.execute('SELECT id, name, color FROM categories WHERE user_id = ?', (user_id,))
    return [dict(row) for row in cursor.fetchall()]