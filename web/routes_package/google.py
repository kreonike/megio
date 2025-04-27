from flask import redirect, url_for, flash, request, session
from flask_login import current_user, login_required
import json
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import datetime as dt
from apscheduler.schedulers.background import BackgroundScheduler
from web.models.models import User
from web.config.config import db_connection


def fetch_google_events(user, max_results=10):
    creds = user.get_google_credentials()
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            return None

    service = build('calendar', 'v3', credentials=creds)
    now = dt.datetime.utcnow().isoformat() + 'Z'

    # Получаем события, включая повторяющиеся
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,  # Разворачиваем повторяющиеся события
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    # Фильтруем события, чтобы избежать дублирования
    unique_events = []
    seen_event_ids = set()
    for event in events:
        event_id = event.get('id')
        if event_id not in seen_event_ids:
            unique_events.append(event)
            seen_event_ids.add(event_id)

    return unique_events


def sync_google_calendar_for_all_users(app):
    logger = logging.getLogger(__name__)
    with app.app_context():
        try:
            with db_connection() as db:
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
                        google_event_ids = set()

                        for event in events:
                            google_event_id = event['id']
                            google_event_ids.add(google_event_id)
                            start = event['start'].get('dateTime', event['start'].get('date'))
                            if not start:
                                continue

                            try:
                                event_date = dt.datetime.fromisoformat(start) if 'T' in start else dt.datetime.strptime(
                                    start, '%Y-%m-%d')
                                if 'date' in event['start']:
                                    event_date = event_date.replace(hour=12, minute=0)

                                # Проверяем, существует ли задача с таким google_event_id
                                cursor.execute('''
                                    SELECT 1 FROM tasks 
                                    WHERE user_id = ? AND google_event_id = ?
                                ''', (user.id, google_event_id))

                                if cursor.fetchone():
                                    continue  # Пропускаем, если событие уже существует

                                cursor.execute('''
                                    INSERT INTO tasks (user_id, year, month, day, task, time, created, google_event_id)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    user.id,
                                    event_date.year,
                                    event_date.month,
                                    event_date.day,
                                    event.get('summary', 'Без названия'),
                                    event_date.strftime('%H:%M') if 'dateTime' in event['start'] else None,
                                    dt.datetime.now(),
                                    google_event_id
                                ))
                                added_count += 1
                            except Exception as e:
                                logger.error(
                                    f"Ошибка при добавлении события для пользователя {user.username}: {str(e)}")
                                continue

                        # Удаляем задачи, которых больше нет в Google Календаре
                        cursor.execute('''
                            SELECT id, google_event_id FROM tasks 
                            WHERE user_id = ? AND google_event_id IS NOT NULL
                        ''', (user.id,))
                        db_tasks = cursor.fetchall()

                        deleted_count = 0
                        for task in db_tasks:
                            if task['google_event_id'] not in google_event_ids:
                                cursor.execute('DELETE FROM tasks WHERE id = ?', (task['id'],))
                                deleted_count += 1

                        db.commit()
                        logger.info(
                            f"Для пользователя {user.username}: добавлено {added_count} новых событий, удалено {deleted_count} событий")

                    except Exception as e:
                        logger.error(f"Ошибка синхронизации для пользователя {user.username}: {str(e)}")
                        continue
        except Exception as e:
            logger.error(f"Ошибка при синхронизации календарей: {str(e)}")


def google_routes(app):
    logger = logging.getLogger(__name__)

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
                        "https://megio.me/oauth2callback"
                    ]
                }
            },
            scopes=app.config['SCOPES'],
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
                scopes=app.config['SCOPES'],
                state=session['oauth_state'],
                redirect_uri=app.config['GOOGLE_REDIRECT_URI']
            )

            flow.fetch_token(authorization_response=request.url)
            credentials = flow.credentials

            with db_connection() as db:
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
        with db_connection() as db:
            cursor = db.cursor()
            cursor.execute('UPDATE users SET google_token = NULL WHERE id = ?', (current_user.id,))
            db.commit()
        flash('Google Calendar успешно отключен', 'success')
        return redirect(url_for('profile'))

    @app.route('/sync_google_calendar')
    @login_required
    def sync_google_calendar():
        events = fetch_google_events(current_user)
        if events is None:
            flash('Не удалось получить доступ к Google Calendar. Пожалуйста, подключите аккаунт.', 'error')
            return redirect(url_for('profile'))

        with db_connection() as db:
            cursor = db.cursor()
            added_count = 0
            google_event_ids = set()

            for event in events:
                google_event_ids.add(event['id'])
                start = event['start'].get('dateTime', event['start'].get('date'))
                if not start:
                    continue

                try:
                    event_date = dt.datetime.fromisoformat(start) if 'T' in start else dt.datetime.strptime(start,
                                                                                                            '%Y-%m-%d')
                    if 'date' in event['start']:
                        event_date = event_date.replace(hour=12, minute=0)

                    cursor.execute('''
                        SELECT 1 FROM tasks 
                        WHERE user_id = ? 
                        AND year = ? AND month = ? AND day = ?
                        AND task = ?
                        AND (time = ? OR (time IS NULL AND ? IS NULL))
                        AND google_event_id = ?
                    ''', (
                        current_user.id,
                        event_date.year,
                        event_date.month,
                        event_date.day,
                        event.get('summary', 'Без названия'),
                        event_date.strftime('%H:%M') if 'dateTime' in event['start'] else None,
                        event_date.strftime('%H:%M') if 'dateTime' in event['start'] else None,
                        event['id']
                    ))

                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO tasks (user_id, year, month, day, task, time, created, google_event_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            current_user.id,
                            event_date.year,
                            event_date.month,
                            event_date.day,
                            event.get('summary', 'Без названия'),
                            event_date.strftime('%H:%M') if 'dateTime' in event['start'] else None,
                            dt.datetime.now(),
                            event['id']
                        ))
                        added_count += 1

                except Exception as e:
                    logger.error(f"Ошибка при добавлении события: {str(e)}")
                    continue

            cursor.execute('''
                SELECT id, google_event_id FROM tasks 
                WHERE user_id = ? AND google_event_id IS NOT NULL
            ''', (current_user.id,))
            db_tasks = cursor.fetchall()

            deleted_count = 0
            for task in db_tasks:
                if task['google_event_id'] not in google_event_ids:
                    cursor.execute('DELETE FROM tasks WHERE id = ?', (task['id'],))
                    deleted_count += 1

            db.commit()
            flash(f'Добавлено {added_count} новых событий, удалено {deleted_count} событий из Google Calendar',
                  'success')
            return redirect(url_for('show_calendar'))


def google_sync_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: sync_google_calendar_for_all_users(app),
        trigger='interval',
        minutes=2
    )
    return scheduler