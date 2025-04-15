# web/routes/remind.py
from flask import request
from flask_login import current_user  # Добавляем импорт
from web.utils import json_response, require_ownership, log_task_action

def remind_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/remind', methods=['POST'])
    @require_ownership(table='tasks')
    def set_task_reminders(year, month, day, db):
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
        log_task_action(app.logger, "set reminders", task_id, current_user.id, year, month, day,
                        extra_info=f"remind_times={remind_times}")
        return json_response(True)