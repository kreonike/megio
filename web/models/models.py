import os
from pathlib import Path
import sqlite3
import secrets  # Добавлен импорт модуля secrets
import json  # Добавлен импорт модуля json
from flask_login import UserMixin
from google.oauth2.credentials import Credentials  # Добавлен импорт Credentials

# Правильный путь к БД:
# От файла models.py (project/web/config/) поднимаемся на 3 уровня вверх (project/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = os.path.join(BASE_DIR, 'database', 'tasks.db')

class User(UserMixin):
    def __init__(self, user_id, username, email, telegram_token=None, google_token=None):
        self.id = user_id
        self.username = username
        self.email = email
        self.telegram_token = telegram_token
        self.google_token = google_token

    def is_telegram_linked(self):
        db = self.get_db()
        cursor = db.cursor()
        cursor.execute('SELECT 1 FROM telegram_users WHERE user_id = ?', (self.id,))
        return cursor.fetchone() is not None

    def generate_telegram_token(self):
        token = secrets.token_urlsafe(16)  # Теперь secrets доступен
        db = self.get_db()
        cursor = db.cursor()
        cursor.execute('UPDATE users SET telegram_token = ? WHERE id = ?', (token, self.id))
        db.commit()
        self.telegram_token = token
        return token

    def get_google_credentials(self):
        if not self.google_token:
            return None
        return Credentials.from_authorized_user_info(json.loads(self.google_token))  # Теперь json и Credentials доступны

    @staticmethod
    def get_db():
        db = sqlite3.connect(DB_PATH, timeout=30)
        db.execute('PRAGMA journal_mode=WAL')
        db.row_factory = sqlite3.Row
        return db

    @classmethod
    def get_by_id(cls, user_id):
        db = cls.get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, username, email, telegram_token, google_token FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return cls(user_data['id'], user_data['username'], user_data['email'],
                      user_data['telegram_token'], user_data['google_token'])
        return None

    @classmethod
    def get_by_username(cls, username):
        db = cls.get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, username, email, password FROM users WHERE username = ?', (username,))
        return cursor.fetchone()

    @classmethod
    def get_by_telegram_token(cls, token):
        db = cls.get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, username, email, telegram_token, google_token FROM users WHERE telegram_token = ?', (token,))
        user_data = cursor.fetchone()
        if user_data:
            return cls(user_data['id'], user_data['username'], user_data['email'],
                      user_data['telegram_token'], user_data['google_token'])
        return None