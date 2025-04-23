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


def log_action(logger, entity, action, user_id, entity_id=None, date=None, **extra_info):
    """
    Универсальная функция для логирования действий над сущностями.

    Args:
        logger: Логгер для записи сообщения.
        entity (str): Тип сущности (например, 'Task', 'Category').
        action (str): Действие (например, 'added', 'deleted').
        user_id: ID пользователя.
        entity_id: ID сущности (опционально).
        date: Словарь с ключами 'year', 'month', 'day' (опционально).
        **extra_info: Дополнительные параметры для включения в лог.
    """
    msg = f"{entity} {entity_id or ''} {action} for user_id={user_id}"
    if date and all(key in date for key in ['year', 'month', 'day']):
        msg += f", date={date['year']}-{date['month']:02d}-{date['day']:02d}"
    for key, value in extra_info.items():
        msg += f", {key}={value}"
    logger.info(msg)


def log_error(logger, message, exc_info=False):
    """
    Логирует ошибку с опциональной информацией об исключении.
    """
    logger.error(message, exc_info=exc_info)


def handle_exceptions(f):
    """
    Декоратор для централизованной обработки исключений и автоматического формирования JSON-ответов.

    - Для успешных вызовов: оборачивает результат в json_response(True, data=result), если результат не является tuple.
    - Для исключений: возвращает JSON с ошибкой и соответствующим статус-кодом.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            # Если результат уже является ответом Flask (например, tuple или Response), возвращаем его
            if isinstance(result, tuple) or isinstance(result, jsonify().__class__):
                return result
            # Для успешного результата формируем JSON-ответ
            return json_response(True, data=result)
        except ValueError as e:
            log_error(logging.getLogger(__name__), f"Value error in {f.__name__}: {str(e)}")
            return json_response(False, error=str(e), status_code=400)
        except PermissionError as e:
            log_error(logging.getLogger(__name__), f"Permission error in {f.__name__}: {str(e)}")
            return json_response(False, error=str(e), status_code=403)
        except Exception as e:
            log_error(logging.getLogger(__name__), f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return json_response(False, error="Внутренняя ошибка сервера", status_code=500)

    return decorated_function