# app.py
import os
import atexit
from datetime import datetime
from flask import Flask, render_template, request, redirect, flash, jsonify, make_response, send_from_directory
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, current_user
from web.logging_config import configure_logging
from web.routes.stats import stats_routes
from web.config.config import init_db, db_connection, MONTH_NAMES
from web.models.models import User
from web.routes.profile import init_profile_routes
from web.routes.telegram import telegram_routes
from web.routes.auth import init_auth_routes
from web.routes.google import google_routes, google_sync_scheduler
from web.routes.categories import categories_routes
from web.routes.remind import remind_routes
from web.routes.complete import complete_routes
from web.routes.tasks import tasks_routes
from web.routes.task_restore import init_task_restore_routes

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)

from web.config.config import (
    SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, SCOPES
)

app.config['GOOGLE_CLIENT_ID'] = GOOGLE_CLIENT_ID
app.config['GOOGLE_CLIENT_SECRET'] = GOOGLE_CLIENT_SECRET
app.config['GOOGLE_REDIRECT_URI'] = GOOGLE_REDIRECT_URI
app.config['SCOPES'] = SCOPES
app.secret_key = SECRET_KEY

bcrypt = Bcrypt(app)

# Настройка логирования
configure_logging(app)
logger = app.logger

# Инициализация маршрутов
init_profile_routes(app)
telegram_routes(app)
init_auth_routes(app, bcrypt)
google_routes(app)
stats_routes(app)
init_task_restore_routes(app)
categories_routes(app)
remind_routes(app)
complete_routes(app)
tasks_routes(app)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Инициализация Google Scheduler
logger.info("Инициализация Google Scheduler...")
if not hasattr(app, 'google_scheduler') and (not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'):
    app.google_scheduler = google_sync_scheduler(app)
    app.google_scheduler.start()
    atexit.register(lambda: app.google_scheduler.shutdown())

# Инициализация базы данных
init_db(app)

# Добавление CSP-заголовка
@app.after_request
def apply_csp(response):
    """
    Добавляет заголовок Content-Security-Policy к каждому ответу.

    Args:
        response: Ответ Flask.

    Returns:
        Модифицированный ответ с заголовком CSP.
    """
    response.headers['Content-Security-Policy'] = (
        "script-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; "
        "object-src 'none'; "
        "default-src 'self'; "
        "connect-src 'self'; "
        "style-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline';"
    )
    return response

# Маршрут для favicon.ico
@app.route('/favicon.ico')
def favicon():
    """
    Возвращает favicon.ico из папки static.

    Returns:
        Файл favicon.ico.
    """
    return send_from_directory(app.static_folder, 'favicon.ico')

@login_manager.user_loader
def load_user(user_id):
    """
    Загружает пользователя по ID для Flask-Login.

    Args:
        user_id: ID пользователя.

    Returns:
        Объект User или None, если пользователь не найден.
    """
    with db_connection() as db:
        cursor = db.cursor()
        cursor.execute('SELECT id, username, email, telegram_token, google_token, timezone FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return User(
                user_id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                telegram_token=user_data['telegram_token'],
                google_token=user_data['google_token'],
                timezone=user_data['timezone']
            )
    return None

if __name__ == '__main__':
    app.run(debug=True)