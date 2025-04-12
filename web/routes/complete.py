from flask import request
from flask_login import login_required, current_user
from web.config.config import db_connection
from web.services.task_service import complete_task
from web.utils import json_response


def complete_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/complete', methods=['POST'])
    @login_required
    def complete_task_endpoint(year, month, day):
        if not request.is_json:
            return json_response(False, error='Invalid content type', status_code=400)

        data = request.get_json()
        task_id = data.get('task_id')

        if not task_id:
            return json_response(False, error='Missing task_id', status_code=400)

        with db_connection() as db:
            try:
                complete_task(db, current_user.id, task_id, year, month, day)
                app.logger.debug(f"Task {task_id} completed for user {current_user.id} on {year}-{month}-{day}")
                return json_response(True)
            except Exception as e:
                app.logger.error(f"Error completing task: {str(e)}", exc_info=True)
                return json_response(False, error=str(e), status_code=500)

    @app.route('/tasks/<int:year>/<int:month>/<int:day>/completed', methods=['GET'])
    @login_required
    def get_completed_tasks(year, month, day):
        with db_connection() as db:
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

                return json_response(True, data={
                    'completed_tasks': completed_tasks,
                    'date': f"{year}-{month:02d}-{day:02d}"
                })
            except Exception as e:
                app.logger.error(f"Error fetching completed tasks: {str(e)}", exc_info=True)
                return json_response(False, error=str(e), status_code=500)