# web/routes/task-restore.py
from flask import jsonify
from flask_login import current_user, login_required
from flask import request

def task_restore_routes(app, get_db):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/restore', methods=['POST'])
    @login_required
    def restore_task(year, month, day):
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Invalid content type'}), 400

        data = request.get_json()
        completed_task_id = data.get('completed_task_id')

        if not completed_task_id:
            return jsonify({'success': False, 'error': 'Missing completed_task_id'}), 400

        db = get_db()
        cursor = db.cursor()

        try:
            # 1. Получаем данные выполненной задачи
            cursor.execute('''
                SELECT task_id, task_text, priority, categories, original_year, original_month, original_day
                FROM completed_tasks
                WHERE id = ? AND user_id = ?
            ''', (completed_task_id, current_user.id))
            completed_task = cursor.fetchone()

            if not completed_task:
                return jsonify({'success': False, 'error': 'Completed task not found'}), 404

            # 2. Восстанавливаем задачу в таблицу tasks
            cursor.execute('''
                INSERT INTO tasks (id, user_id, year, month, day, task, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                completed_task['task_id'],
                current_user.id,
                completed_task['original_year'],
                completed_task['original_month'],
                completed_task['original_day'],
                completed_task['task_text'],
                completed_task['priority']
            ))

            # 3. Восстанавливаем категории (если есть)
            if completed_task['categories']:
                category_names = completed_task['categories'].split(',')
                for category_name in category_names:
                    cursor.execute('''
                        SELECT id FROM categories WHERE user_id = ? AND name = ?
                    ''', (current_user.id, category_name.strip()))
                    category = cursor.fetchone()
                    if category:
                        cursor.execute('''
                            INSERT OR IGNORE INTO task_categories (task_id, category_id)
                            VALUES (?, ?)
                        ''', (completed_task['task_id'], category['id']))

            # 4. Удаляем задачу из completed_tasks
            cursor.execute('DELETE FROM completed_tasks WHERE id = ?', (completed_task_id,))

            db.commit()

            return jsonify({'success': True})

        except Exception as e:
            db.rollback()
            app.logger.error(f"Ошибка при восстановлении задачи: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500