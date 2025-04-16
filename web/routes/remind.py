# web/routes/remind.py
from flask import request
from flask_login import current_user
from web.utils import json_response, require_ownership, log_action, handle_exceptions, validate_date


def remind_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/remind', methods=['POST'])
    @require_ownership(table='tasks')
    @handle_exceptions
    def set_task_reminders(year, month, day, db):
        year, month, day = validate_date(year, month, day)
        data = request.get_json()
        task_id = data.get('task_id')
        remind_times = data.get('remind_times', [])
        app.logger.debug(f"Received remind request: task_id={task_id}, remind_times={remind_times}")

        cursor = db.cursor()
        cursor.execute('''
            UPDATE tasks 
            SET 
                reminder_15m_sent = ?,
                reminder_2h_sent = ?,
                reminder_1day_sent = ?
            WHERE id = ?
        ''', (
            0 if 15 in remind_times else 1,
            0 if 120 in remind_times else 1,
            0 if 1440 in remind_times else 1,
            task_id
        ))

        db.commit()
        log_action(app.logger, "Task", "set reminders", current_user.id, entity_id=task_id,
                   extra_info={'date': {'year': year, 'month': month, 'day': day}, 'remind_times': remind_times})
        return True