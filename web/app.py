
from logging_config import configure_logging
from flask import Flask, render_template, request, redirect, url_for, flash, g, session, json, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import sqlite3
from datetime import datetime
import calendar
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Отключает проверку HTTPS (только для разработки!)
from pathlib import Path
import secrets
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import datetime as dt
from dotenv import load_dotenv
import re
from models.models import User
from web.routes.profile import profile_routes
from web.routes.telegram import telegram_routes
from web.routes.register import register_routes
from web.routes.login import login_routes


from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Импорт конфигурации
from config.config import (
    SECRET_KEY, DB_PATH, BASE_DIR,
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, SCOPES,
    MONTH_NAMES, get_db, close_db
)

atexit.register(lambda: scheduler.shutdown())

# Инициализация приложения
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = SECRET_KEY

# Инициализация маршрутов профиля
profile_routes(app, get_db)
telegram_routes(app, get_db)
register_routes(app, get_db, bcrypt)
login_routes(app, get_db, bcrypt)


# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Инициализация Bcrypt
bcrypt = Bcrypt(app)

# Настройка логирования
configure_logging(app)
logger = app.logger

# Конфигурация Google OAuth
app.config['GOOGLE_CLIENT_ID'] = GOOGLE_CLIENT_ID
app.config['GOOGLE_CLIENT_SECRET'] = GOOGLE_CLIENT_SECRET
app.config['GOOGLE_REDIRECT_URI'] = GOOGLE_REDIRECT_URI


def sync_google_calendar_for_all_users():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, username, email, google_token FROM users WHERE google_token IS NOT NULL')
        users = cursor.fetchall()

        for user_data in users:
            user = User(user_data['id'], user_data['username'], user_data['email'],
                        google_token=user_data['google_token'])
            try:
                events = fetch_google_events(user)
                if events is None:
                    continue

                added_count = 0

                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    if not start:
                        continue

                    try:
                        event_date = dt.datetime.fromisoformat(start) if 'T' in start else dt.datetime.strptime(start,
                                                                                                                '%Y-%m-%d')
                        if 'date' in event['start']:
                            event_date = event_date.replace(hour=12, minute=0)

                        # Проверка на существующее событие
                        cursor.execute('''
                            SELECT 1 FROM tasks 
                            WHERE user_id = ? 
                            AND year = ? AND month = ? AND day = ?
                            AND task = ?
                            AND (time = ? OR (time IS NULL AND ? IS NULL))
                        ''', (
                            user.id,
                            event_date.year,
                            event_date.month,
                            event_date.day,
                            event.get('summary', 'Без названия'),
                            event_date.strftime('%H:%M') if 'dateTime' in event['start'] else None,
                            event_date.strftime('%H:%M') if 'dateTime' in event['start'] else None
                        ))

                        if not cursor.fetchone():
                            cursor.execute('''
                                INSERT INTO tasks (user_id, year, month, day, task, time, created)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                user.id,
                                event_date.year,
                                event_date.month,
                                event_date.day,
                                event.get('summary', 'Без названия'),
                                event_date.strftime('%H:%M') if 'dateTime' in event['start'] else None,
                                dt.datetime.now()
                            ))
                            added_count += 1
                    except Exception as e:
                        logger.error(f"Ошибка при добавлении события для пользователя {user.username}: {str(e)}")
                        continue

                db.commit()
                logger.info(
                    f"Для пользователя {user.username} добавлено {added_count} новых событий из Google Calendar")

            except Exception as e:
                logger.error(f"Ошибка синхронизации для пользователя {user.username}: {str(e)}")
                continue


# Инициализация планировщика
scheduler = BackgroundScheduler()
scheduler.add_job(func=sync_google_calendar_for_all_users, trigger='interval', minutes=2)
scheduler.start()


# Функции для работы с БД
# def get_db():
#     if 'db' not in g:
#         g.db = sqlite3.connect(DB_PATH, timeout=30)
#         g.db.execute('PRAGMA journal_mode=WAL')
#         g.db.row_factory = sqlite3.Row
#     return g.db
#
# def close_db(e=None):
#     db = g.pop('db', None)
#     if db is not None:
#         db.close()

app.teardown_appcontext(close_db)

# Инициализация БД
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            telegram_token TEXT UNIQUE,
            google_token TEXT
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            day INTEGER NOT NULL,
            task TEXT NOT NULL,
            time TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            repeat_days INTEGER DEFAULT NULL,
            repeat_start TEXT DEFAULT NULL,
            repeat_end TEXT DEFAULT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS telegram_users (
            telegram_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )''')
        db.commit()

        cursor.execute('PRAGMA table_info(tasks)')
        columns = [row[1] for row in cursor.fetchall()]

        if 'repeat_days' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN repeat_days INTEGER DEFAULT NULL')
        if 'repeat_start' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN repeat_start TEXT DEFAULT NULL')
        if 'repeat_end' not in columns:
            cursor.execute('ALTER TABLE tasks ADD COLUMN repeat_end TEXT DEFAULT NULL')
        db.commit()

init_db()



@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, username, email, telegram_token, google_token FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['email'],
                   user_data['telegram_token'], user_data['google_token'])

def generate_calendar(year, month, user_id):
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    now = datetime.now()
    current_day = now.day if (year == now.year and month == now.month) else None

    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT day, COUNT(*) as task_count FROM tasks 
        WHERE user_id = ? AND year = ? AND month = ?
        GROUP BY day
    ''', (user_id, year, month))
    days_tasks = {row['day']: row['task_count'] for row in cursor.fetchall()}

    calendar_html = '<table class="calendar-table"><tr>'
    calendar_html += ''.join(f'<th>{day}</th>' for day in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'])
    calendar_html += '</tr>'

    for week in month_days:
        calendar_html += '<tr>'
        for i, day in enumerate(week):
            if day == 0:
                calendar_html += '<td class="empty-day"></td>'
                continue

            classes = ['day-cell']
            if day == current_day:
                classes.append('today')
            if day in days_tasks:
                classes.append('has-tasks')
            if i >= 5:
                classes.append('weekend')

            task_count_html = f'<span class="task-count-badge">{days_tasks[day]}</span>' if day in days_tasks else ''

            calendar_html += f'''
                <td class="{" ".join(classes)}">
                    <a href="{url_for("day_tasks", year=year, month=month, day=day)}" class="day-link" data-day="{day}">
                        <span class="day-number">{day}</span>
                        {task_count_html}
                    </a>
                </td>
            '''
        calendar_html += '</tr>'

    calendar_html += '</table>'
    return calendar_html


@app.route('/')
@login_required
def show_calendar():
    now = datetime.now()
    year = request.args.get('year', default=now.year, type=int)
    month = request.args.get('month', default=now.month, type=int)

    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1

    # Получаем задачи на ближайшие 7 дней
    db = get_db()
    cursor = db.cursor()
    start_date = now.date()
    end_date = start_date + dt.timedelta(days=7)

    cursor.execute('''
        SELECT year, month, day, task, time 
        FROM tasks 
        WHERE user_id = ? 
        AND date(year || '-' || substr('0' || month, -2) || '-' || substr('0' || day, -2)) 
            BETWEEN date(?) AND date(?)
        ORDER BY year, month, day, time
    ''', (current_user.id, start_date.isoformat(), end_date.isoformat()))

    upcoming_tasks = {}
    for task in cursor.fetchall():
        date_str = f"{task['day']}.{task['month']}.{task['year']}"
        if date_str not in upcoming_tasks:
            upcoming_tasks[date_str] = []
        upcoming_tasks[date_str].append({
            'task': task['task'],
            'time': task['time']
        })

    calendar_html = generate_calendar(year, month, current_user.id)
    return render_template('calendar.html',
                           calendar=calendar_html,
                           year=year,
                           month=month,
                           russian_month_name=MONTH_NAMES[month],
                           username=current_user.username,
                           upcoming_tasks=upcoming_tasks)


@app.route('/tasks/<int:year>/<int:month>/<int:day>', methods=['GET', 'POST'])
@login_required
def day_tasks(year, month, day):
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        if 'delete' in request.form:
            task_id = request.form.get('delete')
            cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, current_user.id))
            db.commit()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json.jsonify({'status': 'success'})
            flash('Задача удалена', 'success')

        elif 'task_id' in request.form:
            task_id = request.form.get('task_id')
            new_task = request.form.get('task')
            new_time = request.form.get('time')
            repeat_days = request.form.get('repeat_days')
            repeat_start = request.form.get('repeat_start')
            repeat_end = request.form.get('repeat_end')

            if new_task:
                # Обновляем основную задачу
                cursor.execute('''
                    UPDATE tasks 
                    SET task = ?, time = ?, 
                        repeat_days = ?, 
                        repeat_start = ?, 
                        repeat_end = ? 
                    WHERE id = ? AND user_id = ?
                ''', (
                    new_task,
                    new_time,
                    repeat_days if repeat_days and int(repeat_days) > 0 else None,
                    repeat_start if repeat_days and int(repeat_days) > 0 else None,
                    repeat_end if repeat_days and int(repeat_days) > 0 else None,
                    task_id,
                    current_user.id
                ))
                db.commit()

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return json.jsonify({'status': 'success'})
                flash('Задача обновлена', 'success')

        else:  # Добавление новой задачи
            task = request.form.get('task')
            time = request.form.get('time')
            if task:
                cursor.execute('''
                    INSERT INTO tasks (user_id, year, month, day, task, time, created)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (current_user.id, year, month, day, task, time, dt.datetime.now()))
                db.commit()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return json.jsonify({'status': 'success'})
                flash('Задача добавлена', 'success')

        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return redirect(url_for('day_tasks', year=year, month=month, day=day))

    # GET-запрос
    cursor.execute('''
        SELECT id, task, time, created, repeat_days, repeat_start, repeat_end 
        FROM tasks 
        WHERE user_id = ? AND year = ? AND month = ? AND day = ? 
        ORDER BY time, created
    ''', (current_user.id, year, month, day))
    tasks = [dict(row) for row in cursor.fetchall()]

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return json.jsonify({'tasks': tasks, 'date': f"{year}-{month:02d}-{day:02d}"})

    date_str = f"{day:02d}.{month:02d}.{year}"
    return render_template('tasks.html', year=year, month=month, day=day, date_str=date_str, tasks=tasks)


@app.route('/tasks/<int:year>/<int:month>/<int:day>/remind', methods=['POST'])
@login_required
def set_task_reminders(year, month, day):
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Invalid content type'}), 400

    data = request.get_json()
    task_id = data.get('task_id')
    remind_times = data.get('remind_times', [])  # Пример: [15, 120, 1440]
    logger.debug(f"Received remind request: task_id={task_id}, remind_times={remind_times}")

    if not task_id or not remind_times:
        return jsonify({'success': False, 'error': 'Missing task_id or remind_times'}), 400

    try:
        db = get_db()
        cursor = db.cursor()

        # Проверяем, принадлежит ли задача текущему пользователю
        cursor.execute('SELECT user_id FROM tasks WHERE id = ?', (task_id,))
        task = cursor.fetchone()
        if not task or task['user_id'] != current_user.id:
            return jsonify({'success': False, 'error': 'Task not found or access denied'}), 403

        # Обновляем флаги напоминаний
        cursor.execute('''
            UPDATE tasks 
            SET 
                reminder_15m_sent = ?,
                reminder_2h_sent = ?,
                reminder_1day_sent = ?
            WHERE id = ?
        ''', (
            0 if 15 in remind_times else 1,   # 15 минут
            0 if 120 in remind_times else 1,   # 2 часа
            0 if 1440 in remind_times else 1,  # 24 часа
            task_id
        ))

        db.commit()
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Ошибка при установке напоминаний: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('login'))


@app.route('/connect_google')
@login_required
def connect_google():
    logger.debug(f"Using redirect_uri: {app.config['GOOGLE_REDIRECT_URI']}")

    session.permanent = True

    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": app.config['GOOGLE_CLIENT_ID'],
                "client_secret": app.config['GOOGLE_CLIENT_SECRET'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [
                    app.config['GOOGLE_REDIRECT_URI'],
                    "http://localhost:5000/oauth2callback",
                    "http://127.0.0.1:5000/oauth2callback"
                ]
            }
        },
        scopes=SCOPES,
        redirect_uri=app.config['GOOGLE_REDIRECT_URI']
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )

    session['oauth_state'] = state
    logger.debug(f"Generated auth URL: {authorization_url}")
    return redirect(authorization_url)


@app.route('/oauth2callback')
@login_required
def oauth2callback():
    logger.debug(f"Received callback with URL: {request.url}")

    if 'oauth_state' not in session:
        logger.error("Missing oauth_state in session")
        flash('Сессия истекла. Пожалуйста, начните процесс авторизации снова.', 'error')
        return redirect(url_for('profile'))

    try:
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": app.config['GOOGLE_CLIENT_ID'],
                    "client_secret": app.config['GOOGLE_CLIENT_SECRET'],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [app.config['GOOGLE_REDIRECT_URI']]
                }
            },
            scopes=SCOPES,
            state=session['oauth_state'],
            redirect_uri=app.config['GOOGLE_REDIRECT_URI']
        )

        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        # Сохраняем токены в БД
        db = get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE users SET google_token = ? WHERE id = ?',
                       (json.dumps({
                           'token': credentials.token,
                           'refresh_token': credentials.refresh_token,
                           'token_uri': credentials.token_uri,
                           'client_id': credentials.client_id,
                           'client_secret': credentials.client_secret,
                           'scopes': credentials.scopes
                       }), current_user.id))
        db.commit()

        flash('Google Calendar успешно подключен', 'success')
        return redirect(url_for('profile'))


    except Exception as e:
        logger.error(f"OAuth error: {str(e)}")
        flash('Ошибка авторизации через Google. Пожалуйста, попробуйте снова.', 'error')
        return redirect(url_for('profile'))


@app.route('/disconnect_google', methods=['POST'])
@login_required
def disconnect_google():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE users SET google_token = NULL WHERE id = ?', (current_user.id,))
    db.commit()
    flash('Google Calendar успешно отключен', 'success')
    return redirect(url_for('profile'))


def fetch_google_events(user, max_results=10):
    creds = user.get_google_credentials()
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None

    service = build('calendar', 'v3', credentials=creds)
    now = dt.datetime.utcnow().isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    return events_result.get('items', [])


@app.route('/sync_google_calendar')
@login_required
def sync_google_calendar():
    events = fetch_google_events(current_user)
    if events is None:
        flash('Не удалось получить доступ к Google Calendar. Пожалуйста, подключите аккаунт.', 'error')
        return redirect(url_for('profile'))

    db = get_db()
    cursor = db.cursor()
    added_count = 0

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        if not start:
            continue

        try:
            event_date = dt.datetime.fromisoformat(start) if 'T' in start else dt.datetime.strptime(start, '%Y-%m-%d')
            if 'date' in event['start']:  # Целодневное событие
                event_date = event_date.replace(hour=12, minute=0)

            # Проверяем, существует ли уже такое событие
            cursor.execute('''
                SELECT 1 FROM tasks 
                WHERE user_id = ? 
                AND year = ? AND month = ? AND day = ?
                AND task = ? 
                AND (time = ? OR (time IS NULL AND ? IS NULL))
            ''', (
                current_user.id,
                event_date.year,
                event_date.month,
                event_date.day,
                event.get('summary', 'Без названия'),
                event_date.strftime('%H:%M') if 'dateTime' in event['start'] else None,
                event_date.strftime('%H:%M') if 'dateTime' in event['start'] else None
            ))

            if not cursor.fetchone():  # Событие еще не существует
                cursor.execute('''
                    INSERT INTO tasks (user_id, year, month, day, task, time, created)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    current_user.id,
                    event_date.year,
                    event_date.month,
                    event_date.day,
                    event.get('summary', 'Без названия'),
                    event_date.strftime('%H:%M') if 'dateTime' in event['start'] else None,
                    dt.datetime.now()
                ))
                added_count += 1

        except Exception as e:
            logger.error(f"Ошибка при добавлении события: {str(e)}")
            continue

    db.commit()
    flash(f'Добавлено {added_count} новых событий из Google Calendar', 'success')
    return redirect(url_for('show_calendar'))


if __name__ == '__main__':
    app.run(debug=True)