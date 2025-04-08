from flask_login import UserMixin
import json
import secrets
from google.oauth2.credentials import Credentials
from web.config.config import DB_PATH
import sqlite3

class User(UserMixin):
    def __init__(self, user_id, username, email, telegram_token=None, google_token=None, timezone='UTC'):
        self.id = user_id
        self.username = username
        self.email = email
        self.telegram_token = telegram_token
        self.google_token = google_token
        self.timezone = timezone

    def is_telegram_linked(self):
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute('SELECT 1 FROM telegram_users WHERE user_id = ?', (self.id,))
        result = cursor.fetchone() is not None
        db.close()
        return result

    def generate_telegram_token(self):
        token = secrets.token_urlsafe(16)
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute('UPDATE users SET telegram_token = ? WHERE id = ?', (token, self.id))
        db.commit()
        db.close()
        self.telegram_token = token
        return token

    def get_google_credentials(self):
        if not self.google_token:
            return None
        try:
            token_data = json.loads(self.google_token)
            return Credentials(
                token=token_data.get('token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri'),
                client_id=token_data.get('client_id'),
                client_secret=token_data.get('client_secret'),
                scopes=token_data.get('scopes')
            )
        except (json.JSONDecodeError, AttributeError):
            return None

    def get_google_token(self):
        return self.google_token

    def set_google_token(self, token):
        db = sqlite3.connect(DB_PATH)
        cursor = db.cursor()
        cursor.execute('UPDATE users SET google_token = ? WHERE id = ?', (token, self.id))
        db.commit()
        db.close()
        self.google_token = token