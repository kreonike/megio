# utils/db.py
import logging
from bot.config.config import get_db_connection  # Абсолютный импорт из bot.utils.config

logger = logging.getLogger("bot")

async def get_user_id_by_telegram_id(telegram_id: int) -> int | None:
    """Получает user_id по telegram_id из таблицы telegram_users"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM telegram_users WHERE telegram_id = ?", (telegram_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Error fetching user_id for telegram_id={telegram_id}: {e}", exc_info=True)
        return None

async def get_user_profile(user_id: int) -> tuple | None:
    """Получает профиль пользователя (username, email) по user_id"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, email FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result if result else None
    except Exception as e:
        logger.error(f"Error fetching profile for user_id={user_id}: {e}", exc_info=True)
        return None