# web/routes/task_restore.py
from flask import jsonify, request
from flask_login import login_required, current_user
from web.config.config import db_connection
from web.utils import json_response

def init_task_restore_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/restore', methods=['POST'])
    @login_required
    def restore_task(year, month, day):
        if not request.is_json:
            return json_response(False, error="Требуется JSON-запрос", status_code=400)

        data = request.get_json()
        completed_task_id = data.get('completed_task_id')

        if not completed_task_id:
            return json_response(False, error="Не указан ID выполненной задачи", status_code=400)

        try:
            with db_connection() as db:
                cursor = db.cursor()
                cursor.execute('''
                    SELECT id, task_id, task_text, priority, categories
                    FROM completed_tasks
                    WHERE id = ? AND user_id = ? AND original_year = ? AND original_month = ? AND original_day = ?
                ''', (completed_task_id, current_user.id, year, month, day))
                completed_task = cursor.fetchone()

                if not completed_task:
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
                    return json_response(
                        False,
                        error="Задача не найдена в выполненных",
                        status_code=404
                    )

                # Восстанавливаем задачу в таблицу tasks
                cursor.execute('''
                    INSERT INTO tasks (user_id, task, year, month, day, priority, categories)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    current_user.id,
                    completed_task['task_text'],
                    year,
                    month,
                    day,
                    completed_task['priority'],
                    completed_task['categories']
                ))
                cursor.execute('DELETE FROM completed_tasks WHERE id = ?', (completed_task_id,))
                db.commit()

                app.logger.info(f"Task {completed_task_id} restored for user_id={current_user.id}, date={year}-{month}-{day}")
                return json_response(True, data={"message": "Задача восстановлена"})
        except Exception as e:
            app.logger.error(f"Error restoring task: {str(e)}", exc_info=True)
            return json_response(False, error=str(e), status_code=500)