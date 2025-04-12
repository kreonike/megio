from flask import request
from flask_login import login_required, current_user
from web.config.config import db_connection
from web.services.task_service import restore_task
from web.utils import json_response


def task_restore_routes(app):
    @app.route('/tasks/<int:year>/<int:month>/<int:day>/restore', methods=['POST'])
    @login_required
    def restore_task_endpoint(year, month, day):
        if not request.is_json:
            return json_response(False, error='Invalid content type', status_code=400)

        data = request.get_json()
        completed_task_id = data.get('completed_task_id')

        if not completed_task_id:
            return json_response(False, error='Missing completed_task_id', status_code=400)

        with db_connection() as db:
            try:
                restore_task(db, current_user.id, completed_task_id, year, month, day)
                return json_response(True)
            except Exception as e:
                app.logger.error(f"Error restoring task: {str(e)}", exc_info=True)
                return json_response(False, error=str(e), status_code=500)