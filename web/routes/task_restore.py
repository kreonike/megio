# web/routes/task_restore.py
from flask import jsonify, request
from flask_login import login_required, current_user
from web.config.config import db_connection
from web.utils import json_response
from web.services.task_service import restore_task

def init_task_restore_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/restore', methods=['POST'])
    @login_required
    def restore_task_route(year, month, day):
        if not request.is_json:
            return json_response(False, error="Требуется JSON-запрос", status_code=400)

        data = request.get_json()
        completed_task_id = data.get('completed_task_id')

        if not completed_task_id:
            return json_response(False, error="Не указан ID выполненной задачи", status_code=400)

        try:
            with db_connection() as db:
                new_task_id = restore_task(db, current_user.id, completed_task_id, year, month, day)
                app.logger.info(f"Task {completed_task_id} restored for user_id={current_user.id}, date={year}-{month}-{day}")
                return json_response(True, data={"message": "Задача восстановлена"})
        except PermissionError as e:
            cursor = db.cursor()
            cursor.execute('''
                SELECT id, task_id, task_text
                FROM completed_tasks
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 10
            ''', (current_user.id,))
            last_tasks = cursor.fetchall()
            app.logger.error(
                f"Задача {completed_task_id} не найдена. "
                f"Последние 10 выполненных задач пользователя: {last_tasks}"
            )
            return json_response(False, error=str(e), status_code=404)
        except Exception as e:
            app.logger.error(f"Error restoring task: {str(e)}", exc_info=True)
            return json_response(False, error=str(e), status_code=500)