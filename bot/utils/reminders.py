# bot/utils/reminders.py (опционально)
from datetime import datetime, timedelta
from aiogram import Bot
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import logging

logger = logging.getLogger("bot")

QUERY_24H = "SELECT id, task, time, telegram_id FROM tasks WHERE year = :year AND month = :month AND day = :day AND reminder_1day_sent = 0"
QUERY_2H = "SELECT id, task, time, telegram_id FROM tasks WHERE year = :year AND month = :month AND day = :day AND reminder_2h_sent = 0"
QUERY_15M = "SELECT id, task, time, telegram_id FROM tasks WHERE year = :year AND month = :month AND day = :day AND reminder_15m_sent = 0"
UPDATE_REMINDER_STATUS = "UPDATE tasks SET {field} = 1 WHERE id = :task_id"
REMINDER_INTERVAL = 30  # Можно оставить в constants.py

async def send_reminder(bot, telegram_id, task_datetime, task_text, reminder_type):
    try:
        if reminder_type == '24h':
            message = (f"🔔 Напоминание (за 24 часа):\n"
                       f"📅 {task_datetime.day:02d}.{task_datetime.month:02d}.{task_datetime.year} "
                       f"в {task_datetime.strftime('%H:%M')}\n"
                       f"📝 {task_text}")
        elif reminder_type == '2h':
            message = (f"🔔 Напоминание (за 2 часа):\n"
                       f"⏰ Сегодня в {task_datetime.strftime('%H:%M')}\n"
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

def parse_task_datetime(year, month, day, time_str):
    try:
        return datetime.strptime(f"{year}-{month:02d}-{day:02d} {time_str}", "%Y-%m-%d %H:%M")
    except ValueError as e:
        logger.error(f"Ошибка парсинга времени: {e}")
        return None

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
                if task_datetime and abs((task_datetime - now).total_seconds() - 86400) < 60:
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
                if task_datetime and abs((task_datetime - now).total_seconds() - 7200) < 60:
                    if await send_reminder(bot, telegram_id, task_datetime, task_text, '2h'):
                        session.execute(
                            text(UPDATE_REMINDER_STATUS.format(field='reminder_2h_sent')),
                            {"task_id": task_id}
                        )
                        session.commit()

            # 3. Напоминания за 15 минут
            result = session.execute(
                text(QUERY_15M),
                {"year": now.year, "month": now.month, "day": now.day}
            ).fetchall()
            for task_id, task_text, task_time, telegram_id in result:
                task_datetime = parse_task_datetime(now.year, now.month, now.day, task_time)
                if task_datetime and abs((task_datetime - now).total_seconds() - 900) < 60:
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