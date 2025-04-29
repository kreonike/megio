from datetime import datetime, timedelta, time
from aiogram import Bot
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import logging
from datetime import time as dtime

logger = logging.getLogger("bot")

QUERY_24H = """
SELECT t.id, t.task, t.time, tu.telegram_id 
FROM tasks t
JOIN users u ON t.user_id = u.id
JOIN telegram_users tu ON u.id = tu.user_id
WHERE t.year = :year AND t.month = :month AND t.day = :day AND t.reminder_1day_sent = 0
"""

QUERY_2H = """
SELECT t.id, t.task, t.time, tu.telegram_id 
FROM tasks t
JOIN users u ON t.user_id = u.id
JOIN telegram_users tu ON u.id = tu.user_id
WHERE t.year = :year AND t.month = :month AND t.day = :day AND t.reminder_2h_sent = 0
"""

QUERY_15M = """
SELECT t.id, t.task, t.time, tu.telegram_id 
FROM tasks t
JOIN users u ON t.user_id = u.id
JOIN telegram_users tu ON u.id = tu.user_id
WHERE t.year = :year AND t.month = :month AND t.day = :day AND t.reminder_15m_sent = 0
"""

UPDATE_REMINDER_STATUS = "UPDATE tasks SET {field} = 1 WHERE id = :task_id"
REMINDER_INTERVAL = 30


async def send_reminder(bot, telegram_id, task_datetime, task_text, reminder_type):
    try:
        time_str = task_datetime.strftime('%H:%M') if task_datetime.time() != time(0, 0) else "в течение дня"

        if reminder_type == '24h':
            message = (f"🔔 Напоминание (за 24 часа):\n"
                       f"📅 {task_datetime.day:02d}.{task_datetime.month:02d}.{task_datetime.year} "
                       f"{time_str}\n"
                       f"📝 {task_text}")
        elif reminder_type == '2h':
            message = (f"🔔 Напоминание (за 2 часа):\n"
                       f"⏰ Сегодня {time_str}\n"
                       f"📝 {task_text}")
        elif reminder_type == '15m':
            message = (f"🔔 Напоминание (за 15 минут):\n"
                       f"⏰ Скоро в {task_datetime.strftime('%H:%M')}\n"
                       f"📝 {task_text}")

        await bot.send_message(telegram_id, message)
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки напоминания ({reminder_type}): {e}")
        return False


def parse_task_datetime(year, month, day, task_time):
    try:
        if task_time is None:
            return datetime(year, month, day)
        if isinstance(task_time, str):
            # Предполагаем, что строка в формате "HH:MM" или "HH:MM:SS"
            try:
                # Разделяем строку на часы, минуты и (если есть) секунды
                time_parts = task_time.split(":")
                hours = int(time_parts[0])
                minutes = int(time_parts[1])
                seconds = int(time_parts[2]) if len(time_parts) > 2 else 0
                task_time = dtime(hours, minutes, seconds)
            except (ValueError, IndexError) as e:
                logger.error(f"Ошибка парсинга строки времени '{task_time}': {e}")
                return None
        elif not isinstance(task_time, dtime):
            logger.error(f"Неподдерживаемый тип времени: {type(task_time)}")
            return None
        return datetime.combine(datetime(year, month, day).date(), task_time)
    except ValueError as e:
        logger.error(f"Ошибка парсинга времени: {e}")
        return None


def should_send_reminder(task_datetime, now, reminder_hours):
    """Проверяет, нужно ли отправлять напоминание"""
    time_diff = (task_datetime - now).total_seconds()
    reminder_seconds = reminder_hours * 3600
    return 0 < time_diff <= reminder_seconds + 60  # +60 секунд для небольшого окна


async def check_reminders(bot: Bot, session: Session, interval: int = REMINDER_INTERVAL):
    logger.info(f"Starting reminders service with interval: {interval} seconds")
    while True:
        try:
            now = datetime.now()

            # 1. Напоминания за 24 часа
            tomorrow = now + timedelta(days=1)
            result = session.execute(
                text(QUERY_24H),
                {"year": tomorrow.year, "month": tomorrow.month, "day": tomorrow.day}
            ).fetchall()

            for task_id, task_text, task_time, telegram_id in result:
                task_datetime = parse_task_datetime(tomorrow.year, tomorrow.month, tomorrow.day, task_time)
                if task_datetime and should_send_reminder(task_datetime, now, 24):
                    if await send_reminder(bot, telegram_id, task_datetime, task_text, '24h'):
                        session.execute(
                            text(UPDATE_REMINDER_STATUS.format(field='reminder_1day_sent')),
                            {"task_id": task_id}
                        )
                        session.commit()

            # 2. Напоминания за 2 часа
            result = session.execute(
                text(QUERY_2H),
                {"year": now.year, "month": now.month, "day": now.day}
            ).fetchall()

            for task_id, task_text, task_time, telegram_id in result:
                task_datetime = parse_task_datetime(now.year, now.month, now.day, task_time)
                if task_datetime and should_send_reminder(task_datetime, now, 2):
                    if await send_reminder(bot, telegram_id, task_datetime, task_text, '2h'):
                        session.execute(
                            text(UPDATE_REMINDER_STATUS.format(field='reminder_2h_sent')),
                            {"task_id": task_id}
                        )
                        session.commit()

            # 3. Напоминания за 15 минут (0.25 часа)
            result = session.execute(
                text(QUERY_15M),
                {"year": now.year, "month": now.month, "day": now.day}
            ).fetchall()

            for task_id, task_text, task_time, telegram_id in result:
                if task_time is not None:  # Только для задач с указанным временем
                    task_datetime = parse_task_datetime(now.year, now.month, now.day, task_time)
                    if task_datetime and should_send_reminder(task_datetime, now, 0.25):
                        if await send_reminder(bot, telegram_id, task_datetime, task_text, '15m'):
                            session.execute(
                                text(UPDATE_REMINDER_STATUS.format(field='reminder_15m_sent')),
                                {"task_id": task_id}
                            )
                            session.commit()

        except Exception as e:
            logger.error(f"Error in reminders loop: {e}")
            session.rollback()
        finally:
            await asyncio.sleep(interval)