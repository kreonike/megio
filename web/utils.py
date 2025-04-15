# web/utils.py

from flask import jsonify, request
from functools import wraps
from flask_login import current_user
from web.services.task_service import check_ownership, PermissionError
from web.config.config import db_connection
import logging


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
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
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


def log_task_action(logger, action, task_id, user_id, year=None, month=None, day=None, extra_info=None):
    """
    Логирует действие над задачей с указанием ID задачи, пользователя и даты.

    Args:
        logger: Объект логгера (например, app.logger).
        action (str): Действие (например, 'restored', 'completed', 'deleted').
        task_id: ID задачи.
        user_id: ID пользователя.
        year, month, day: Дата действия (опционально).
        extra_info: Дополнительная информация (опционально).
    """
    date_str = f"date={year}-{month:02d}-{day:02d}" if year and month and day else ""
    msg = f"Task {task_id} {action} for user_id={user_id}"
    if date_str:
        msg += f", {date_str}"
    if extra_info:
        msg += f", info={extra_info}"
    logger.info(msg)


def log_category_action(logger, action, category_id, user_id, name=None):
    """
    Логирует действие над категорией.

    Args:
        logger: Объект логгера.
        action (str): Действие (например, 'added', 'deleted').
        category_id: ID категории (или None, если категория только создана).
        user_id: ID пользователя.
        name: Название категории (опционально).
    """
    msg = f"Category {action} for user_id={user_id}"
    if category_id:
        msg += f", category_id={category_id}"
    if name:
        msg += f", name={name}"
    logger.info(msg)


def log_error(logger, message, exc_info=False):
    """
    Логирует ошибку с опциональной информацией об исключении.

    Args:
        logger: Объект логгера.
        message (str): Сообщение об ошибке.
        exc_info (bool): Включать ли информацию об исключении.
    """
    logger.error(message, exc_info=exc_info)