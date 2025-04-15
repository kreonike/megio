# web/routes/task_restore.py
from flask import request
from flask_login import current_user
from web.utils import json_response, require_ownership, log_task_action, log_error, handle_exceptions
from web.services.task_service import restore_task

def init_task_restore_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/restore', methods=['POST'])
    @require_ownership(table='completed_tasks', id_field='completed_task_id')
    @handle_exceptions
    def restore_task_route(year, month, day, db):
        data = request.get_json()
        completed_task_id = data.get('completed_task_id')
        new_task_id = restore_task(db, current_user.id, completed_task_id, year, month, day)
        log_task_action(app.logger, "restored", completed_task_id, current_user.id, year, month, day)
        return json_response(True, data={"message": "Задача восстановлена"})