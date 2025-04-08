import sqlite3
import os
from pathlib import Path
import logging

logger = logging.getLogger("bot")

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR.parent / 'database'  # Using Path instead of os.path
DB_PATH = DB_DIR / 'tasks.db'          # Using Path instead of os.path
DB_TIMEOUT = 30


def get_db_connection():
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # Using Path methods
        conn = sqlite3.connect(str(DB_PATH), timeout=30)   # str() for compatibility
        conn.execute('PRAGMA journal_mode=WAL')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.critical(f"Database connection failed: {str(e)}")
        raise