# web/routes/task_restore.py
from flask import request
from flask_login import current_user
from web.utils import json_response, require_ownership, log_action, log_error, handle_exceptions, validate_date
from web.services.task_service import restore_task


def init_task_restore_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/restore', methods=['POST'])
    @require_ownership(table='completed_tasks', id_field='completed_task_id')
    @handle_exceptions
    def restore_task_route(year, month, day, db):
        year, month, day = validate_date(year, month, day)
        data = request.get_json()
        completed_task_id = data.get('completed_task_id')
        new_task_id = restore_task(db, current_user.id, completed_task_id, year, month, day)
        log_action(app.logger, "Task", "restored", current_user.id, entity_id=completed_task_id,
                   extra_info={'date': {'year': year, 'month': month, 'day': day}})
        return {"message": "Задача восстановлена"}