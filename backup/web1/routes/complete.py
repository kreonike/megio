from flask import jsonify, request
from flask_login import login_required, current_user
from web.config.config import get_db

def complete_routes(app, get_db):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/complete', methods=['POST'])
    @login_required
    def complete_task(year, month, day):
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Invalid content type'}), 400

        data = request.get_json()
        task_id = data.get('task_id')

        if not task_id:
            return jsonify({'success': False, 'error': 'Missing task_id'}), 400

        db = get_db()
        cursor = db.cursor()

        try:
            # 1. Получаем данные задачи
            cursor.execute('''
                SELECT id, user_id, task, priority
                FROM tasks
                WHERE id = ? AND user_id = ?
            ''', (task_id, current_user.id))
            task = cursor.fetchone()

            if not task:
                return jsonify({'success': False, 'error': 'Task not found'}), 404

            # 2. Получаем категории задачи
            cursor.execute('''
                SELECT c.name
                FROM categories c
                JOIN task_categories tc ON c.id = tc.category_id
                WHERE tc.task_id = ?
            ''', (task_id,))
            categories = [row['name'] for row in cursor.fetchall()]

            # 3. Переносим в таблицу выполненных задач с правильными именами столбцов
            cursor.execute('''
                INSERT INTO completed_tasks
                (user_id, task_id, task_text, priority, categories, original_year, original_month, original_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                current_user.id,
                task_id,
                task['task'],
                task['priority'],
                ','.join(categories) if categories else None,
                year,
                month,
                day
            ))

            # 4. Удаляем из текущих задач
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

            # 5. Удаляем связи с категориями
            cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))

            db.commit()

            return jsonify({'success': True})

        except Exception as e:
            db.rollback()
            app.logger.error(f"Ошибка при выполнении задачи: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/tasks/<int:year>/<int:month>/<int:day>/completed', methods=['GET'])
    @login_required
    def get_completed_tasks(year, month, day):
        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute('''
                SELECT id, task_id, task_text, priority, categories,
                       datetime(completion_time, 'localtime') as completion_time
                FROM completed_tasks
                WHERE user_id = ? AND original_year = ? AND original_month = ? AND original_day = ?
                ORDER BY completion_time DESC
            ''', (current_user.id, year, month, day))

            completed_tasks = [dict(row) for row in cursor.fetchall()]

            return jsonify({
                'completed_tasks': completed_tasks,
                'date': f"{year}-{month:02d}-{day:02d}"
            })
        except Exception as e:
            app.logger.error(f"Error fetching completed tasks: {str(e)}")
            return jsonify({'error': str(e)}), 500