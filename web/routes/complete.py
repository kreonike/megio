# web/routes/complete.py
from flask import jsonify, request
from flask_login import login_required, current_user
from web.config.config import db_connection
from web.utils import json_response
from web.services.task_service import complete_task

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
    def complete_task_route(year, month, day):
        if not request.is_json:
            return json_response(False, error="Требуется JSON-запрос", status_code=400)

        data = request.get_json()
        task_id = data.get('task_id')

        if not task_id:
            return json_response(False, error="Не указан ID задачи", status_code=400)

        try:
            with db_connection() as db:
                completed_id = complete_task(db, current_user.id, task_id, year, month, day)
                app.logger.info(f"Task {task_id} marked as completed for user_id={current_user.id}, date={year}-{month}-{day}")
                return json_response(True, data={"message": "Задача отмечена как выполненная"})
        except PermissionError as e:
            app.logger.error(f"Task {task_id} not found or access denied")
            return json_response(False, error=str(e), status_code=404)
        except Exception as e:
            app.logger.error(f"Error completing task: {str(e)}", exc_info=True)
            return json_response(False, error=str(e), status_code=500)