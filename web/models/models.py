# web/models/models.py
from flask_login import UserMixin
import json
import secrets
from google.oauth2.credentials import Credentials
from web.config.config import DB_PATH
import sqlite3

class User(UserMixin):
    def __init__(self, user_id, username, email, telegram_token=None, google_token=None):
        self.id = user_id
        self.username = username
        self.email = email
        self.telegram_token = telegram_token
        self.google_token = google_token

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
        return Credentials.from_authorized_user_info(json.loads(self.google_token))