from flask import jsonify, request
from flask_login import login_required, current_user
from web.config.config import db_connection
from web.utils import json_response
from web.services.task_service import check_ownership

def remind_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/remind', methods=['POST'])
    @login_required
    def set_task_reminders(year, month, day):
        if not request.is_json:
            return json_response(False, error='Invalid content type', status_code=400)

        data = request.get_json()
        task_id = data.get('task_id')
        remind_times = data.get('remind_times', [])  # Пример: [15, 120, 1440]
        app.logger.debug(f"Received remind request: task_id={task_id}, remind_times={remind_times}")

        if not task_id or not remind_times:
            return json_response(False, error='Missing task_id or remind_times', status_code=400)

        try:
            with db_connection() as db:
                cursor = db.cursor()

                # Проверяем права доступа
                check_ownership(cursor, 'tasks', task_id, current_user.id)

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
                return json_response(True)

        except PermissionError as e:
            app.logger.error(f"Permission error: {str(e)}")
            return json_response(False, error=str(e), status_code=403)
        except Exception as e:
            app.logger.error(f"Ошибка при установке напоминаний: {str(e)}")
            return json_response(False, error=str(e), status_code=500)