# web/utils.py
from flask import jsonify, request, redirect, url_for, flash
from functools import wraps
from flask_login import current_user
from web.services.task_service import check_ownership, PermissionError
from web.config.config import db_connection
import logging
from datetime import datetime


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


def handle_crud_post(action_handlers, redirect_endpoint, ajax_response_data=None):
    """
    Декоратор для обработки CRUD POST-запросов.

    Args:
        action_handlers (dict or callable): Словарь обработчиков или функция, возвращающая словарь,
                                           где ключи — действия ('delete', 'add', 'update'),
                                           а значения — функции, возвращающие (success, flash_data).
        redirect_endpoint (str): Имя конечной точки для редиректа.
        ajax_response_data (callable, optional): Функция для формирования данных AJAX-ответа.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                @handle_exceptions
                def process_post():
                    # Если action_handlers — функция, вызываем ее только с year, month, day
                    handlers = action_handlers(kwargs.get('year'), kwargs.get('month'), kwargs.get('day')) if callable(action_handlers) else action_handlers
                    for action, handler in handlers.items():
                        if (action == 'delete' and 'delete' in request.form) or \
                           (action == 'add' and 'task' in request.form and 'task_id' not in request.form) or \
                           (action == 'update' and 'task_id' in request.form):
                            return handler()
                    raise ValueError('Недопустимое действие')

                success, flash_data = process_post()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return json_response(success, data=ajax_response_data(flash_data) if ajax_response_data and success else None, error=flash_data.get('message') if not success else None)
                if success:
                    flash(flash_data['message'], flash_data['category'])
                else:
                    flash(flash_data.get('message', 'Ошибка при выполнении действия'), 'error')
                return redirect(url_for(redirect_endpoint, **kwargs))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_action(logger, entity, action, user_id, entity_id=None, extra_info=None):
    """
    Универсальная функция для логирования действий над сущностями.
    """
    msg = f"{entity} {entity_id or ''} {action} for user_id={user_id}"
    if extra_info:
        for key, value in extra_info.items():
            if key == 'date' and isinstance(value, dict) and all(k in value for k in ['year', 'month', 'day']):
                msg += f", date={value['year']}-{value['month']:02d}-{value['day']:02d}"
            else:
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
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            if isinstance(result, tuple) or isinstance(result, jsonify().__class__):
                return result
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


def validate_date(year, month, day, redirect_endpoint=None):
    """
    Проверяет и корректирует параметры даты.
    """
    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1
    if year < 1900 or year > 9999:
        now = datetime.now()
        if redirect_endpoint:
            return redirect(url_for(redirect_endpoint, year=now.year, month=now.month))
        raise ValueError("Invalid year")
    return year, month, day