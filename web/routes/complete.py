# web/routes/complete.py
from flask import jsonify, request
from flask_login import login_required, current_user
from web.config.config import db_connection
from web.utils import json_response
from datetime import datetime

def complete_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/completed', methods=['GET'])
    @login_required
    def get_completed_tasks(year, month, day):
        try:
            with db_connection() as db:
                cursor = db.cursor()
                cursor.execute('''
                    SELECT id, task_id, task_text, priority, categories, completion_time
                    FROM completed_tasks
                    WHERE user_id = ? AND original_year = ? AND original_month = ? AND original_day = ?
                ''', (current_user.id, year, month, day))
                completed_tasks = [
                    {
                        'id': row['id'],
                        'task_id': row['task_id'],
                        'task_text': row['task_text'],
                        'priority': row['priority'],
                        'categories': row['categories'],
                        'completion_time': row['completion_time']
                    }
                    for row in cursor.fetchall()
                ]
                app.logger.info(f"Fetched {len(completed_tasks)} completed tasks for user_id={current_user.id}, date={year}-{month}-{day}")
                return json_response(True, data={'completedTasks': completed_tasks})
        except Exception as e:
            app.logger.error(f"Error fetching completed tasks: {str(e)}", exc_info=True)
            return json_response(False, error=str(e), status_code=500)

    @app.route('/tasks/<int:year>/<int:month>/<int:day>/complete', methods=['POST'])
    @login_required
    def complete_task(year, month, day):
        if not request.is_json:
            return json_response(False, error="Требуется JSON-запрос", status_code=400)

        data = request.get_json()
        task_id = data.get('task_id')

        if not task_id:
            return json_response(False, error="Не указан ID задачи", status_code=400)

        try:
            with db_connection() as db:
                cursor = db.cursor()
                cursor.execute('''
                    SELECT id, task, priority, categories
                    FROM tasks
                    WHERE id = ? AND user_id = ?
                ''', (task_id, current_user.id))
                task = cursor.fetchone()

                if not task:
                    return json_response(False, error="Задача не найдена", status_code=404)

                # Записываем задачу в completed_tasks
                cursor.execute('''
                    INSERT INTO completed_tasks (
                        user_id, task_id, task_text, priority, categories,
                        original_year, original_month, original_day, completion_time
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    current_user.id,
                    task_id,
                    task['task'],
                    task['priority'],
                    task['categories'],
                    year,
                    month,
                    day,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
                db.commit()

                app.logger.info(f"Task {task_id} marked as completed for user_id={current_user.id}, date={year}-{month}-{day}")
                return json_response(True, data={"message": "Задача отмечена как выполненная"})
        except Exception as e:
            app.logger.error(f"Error completing task: {str(e)}", exc_info=True)
            return json_response(False, error=str(e), status_code=500)