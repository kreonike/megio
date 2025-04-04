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

def sync_google_calendar_for_all_users(app, get_db):
    logger = logging.getLogger(__name__)
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
                        event_date = dt.datetime.fromisoformat(start) if 'T' in start else dt.datetime.strptime(start, '%Y-%m-%d')
                        if 'date' in event['start']:
                            event_date = event_date.replace(hour=12, minute=0)

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
                logger.info(f"Для пользователя {user.username} добавлено {added_count} новых событий из Google Calendar")

            except Exception as e:
                logger.error(f"Ошибка синхронизации для пользователя {user.username}: {str(e)}")
                continue

def google_routes(app, get_db):
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
                        "http://127.0.0.1:5000/oauth2callback"
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
                if 'date' in event['start']:
                    event_date = event_date.replace(hour=12, minute=0)

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

                if not cursor.fetchone():
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



def google_sync_scheduler(app, get_db):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=lambda: sync_google_calendar_for_all_users(app, get_db),
        trigger='interval',
        minutes=2
    )
    return scheduler