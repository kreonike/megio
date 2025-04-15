# web/routes/complete.py
from flask import request, jsonify
from flask_login import login_required, current_user
from web.utils import json_response, require_ownership, log_task_action, log_error, handle_exceptions
from web.services.task_service import complete_task
from web.config.config import db_connection

def complete_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/complete', methods=['POST'])
    @require_ownership(table='tasks')
    @handle_exceptions
    def complete_task_route(year, month, day, db):
        data = request.get_json()
        task_id = data.get('task_id')
        completed_id = complete_task(db, current_user.id, task_id, year, month, day)
        log_task_action(app.logger, "marked as completed", task_id, current_user.id, year, month, day)
        return json_response(True, data={"message": "Задача отмечена как выполненная"})

    @app.route('/tasks/<int:year>/<int:month>/<int:day>/completed', methods=['GET'])
    @login_required
    @handle_exceptions
    def get_completed_tasks(year, month, day):
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
            log_task_action(app.logger, "fetched completed tasks", None, current_user.id, year, month, day,
                            extra_info=f"count={len(completed_tasks)}")
            return json_response(True, data={'completedTasks': completed_tasks})