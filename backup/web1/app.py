import calendar
import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, flash, json, jsonify
from flask import url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, current_user

from web.logging_config import configure_logging
from web.routes.stats import stats_routes

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
import datetime as dt
from web.config.config import init_db

from web.models.models import User
from web.routes.profile import profile_routes
from web.routes.telegram import telegram_routes
from web.routes.register import register_routes
from web.routes.login import login_routes
from web.routes.logout import logout_routes
from web.routes.google import google_routes, google_sync_scheduler
#from web.routes.categories import categories_routes
from web.routes.task_restore import task_restore_routes
from web.routes.categories import categories_routes
from web.routes.remind import remind_routes
from web.routes.calendar import generate_calendar
from web.routes.complete import complete_routes
from web.routes.tasks import tasks_routes


import atexit

# Импорт конфигурации
from web.config.config import (
    SECRET_KEY, MONTH_NAMES, get_db, close_db
)

app = Flask(__name__)

from web.config.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, SCOPES

app.config['GOOGLE_CLIENT_ID'] = GOOGLE_CLIENT_ID
app.config['GOOGLE_CLIENT_SECRET'] = GOOGLE_CLIENT_SECRET
app.config['GOOGLE_REDIRECT_URI'] = GOOGLE_REDIRECT_URI
app.config['SCOPES'] = SCOPES

bcrypt = Bcrypt(app)
app.secret_key = SECRET_KEY



# Настройка логирования
configure_logging(app)
logger = app.logger

# Инициализация маршрутов
profile_routes(app, get_db)
telegram_routes(app, get_db)
register_routes(app, get_db, bcrypt)
login_routes(app, get_db, bcrypt)
logout_routes(app)
google_routes(app, get_db)
stats_routes(app, get_db)
task_restore_routes(app, get_db)
categories_routes(app)
remind_routes(app)
complete_routes(app, get_db)
tasks_routes(app, get_db)
#categories_routes(app, get_db)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Инициализация Google Scheduler
logger.info("Initializing Google Scheduler...")
if not hasattr(app, 'google_scheduler') and (not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'):
    app.google_scheduler = google_sync_scheduler(app, get_db)
    app.google_scheduler.start()
    atexit.register(lambda: app.google_scheduler.shutdown())

app.teardown_appcontext(close_db)
init_db(app)


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, username, email, telegram_token, google_token FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['email'],
                    user_data['telegram_token'], user_data['google_token'])



if __name__ == '__main__':
    app.run(debug=True)
