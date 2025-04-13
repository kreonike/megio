# web/utils.py
from flask import jsonify, request
from functools import wraps
from flask_login import current_user
from web.services.task_service import check_ownership, PermissionError
from web.config.config import db_connection

def json_response(success=True, data=None, error=None, status_code=200):
    response = {'success': success}
    if data is not None:
        response['data'] = data
    if error is not None:
        response['error'] = error
    return jsonify(response), status_code

def require_ownership(table, id_field='task_id'):
    """
    Декоратор для проверки прав доступа к записи в указанной таблице.

    Args:
        table (str): Название таблицы (например, 'tasks', 'completed_tasks').
        id_field (str): Поле в JSON-запросе, содержащее ID записи (по умолчанию 'task_id').

    Returns:
        Декорированная функция с проверкой прав доступа.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Проверяем, аутентифицирован ли пользователь
            if not current_user.is_authenticated:
                return json_response(False, error="Требуется авторизация", status_code=401)

            if not request.is_json:
                return json_response(False, error="Требуется JSON-запрос", status_code=400)

            data = request.get_json()
            record_id = data.get(id_field)

            if not record_id:
                return json_response(False, error=f"Не указан {id_field}", status_code=400)

            try:
                with db_connection() as db:
                    cursor = db.cursor()
                    check_ownership(cursor, table, record_id, current_user.id)
                    return f(*args, **kwargs, db=db)
            except PermissionError as e:
                return json_response(False, error=str(e), status_code=403)
            except Exception as e:
                return json_response(False, error=str(e), status_code=500)
        return decorated_function
    return decorator