# config/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent  # Поднимаемся на уровень выше до web/
DB_DIR = os.path.join(BASE_DIR, '..', 'database')  # Добавляем переход на уровень выше для доступа к project/database
DB_PATH = os.path.join(DB_DIR, 'tasks.db')  # Или 'tasks.py', если это действительно файл Python
DB_TIMEOUT = 30

# Настройки приложения
SECRET_KEY = os.getenv('SECRET_KEY')

# Настройки Google OAuth
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Русские названия месяцев
MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}