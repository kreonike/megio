from flask import jsonify, request
from flask_login import login_required, current_user
from web.config.config import db_connection

def remind_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/remind', methods=['POST'])
    @login_required
    def set_task_reminders(year, month, day):
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Invalid content type'}), 400

        data = request.get_json()
        task_id = data.get('task_id')
        remind_times = data.get('remind_times', [])  # Пример: [15, 120, 1440]
        app.logger.debug(f"Received remind request: task_id={task_id}, remind_times={remind_times}")

        if not task_id or not remind_times:
            return jsonify({'success': False, 'error': 'Missing task_id or remind_times'}), 400

        try:
            with db_connection() as db:
                cursor = db.cursor()

                cursor.execute('SELECT user_id FROM tasks WHERE id = ?', (task_id,))
                task = cursor.fetchone()
                if not task or task['user_id'] != current_user.id:
                    return jsonify({'success': False, 'error': 'Task not found or access denied'}), 403

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
                return jsonify({'success': True})

        except Exception as e:
            app.logger.error(f"Ошибка при установке напоминаний: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500