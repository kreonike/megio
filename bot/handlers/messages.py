from aiogram import types, F
from datetime import datetime
from bot.utils.db import get_user_id_by_telegram_id
from bot.config.config import get_db_connection
from bot.utils.calendar import show_day_tasks
from bot.utils.state import user_states, UserState
import re
import logging

logger = logging.getLogger("bot")


async def handle_text_message(message: types.Message):
    telegram_id = message.from_user.id
    if telegram_id not in user_states:
        user_states[telegram_id] = UserState()
    user_state = user_states[telegram_id]

    if user_state.awaiting_task_text and user_state.current_date:
        year, month, day = user_state.current_date
        user_id = await get_user_id_by_telegram_id(telegram_id)

        if not user_id:
            await message.answer("🔐 Ошибка авторизации. Привяжите Telegram ID на сайте.")
            return

        task_text = message.text.strip()

        # Проверяем формат "ЧЧ:ММ Текст задачи"
        time_match = re.match(r'^(\d{1,2})\s*:\s*(\d{2})\s+(.+)$', task_text)

        if not time_match:
            await message.answer(
                "❌ Неверный формат. Введите задачу в формате:\n"
                "<b>ЧЧ:ММ Текст задачи</b>\n"
                "Пример: <code>15:00 Встреча с клиентом</code>\n"
                "Или: <code>9 :30 Утренний кофе</code>",
                parse_mode="HTML"
            )
            return

        try:
            hours, minutes, task_description = time_match.groups()
            hours = int(hours)
            minutes = int(minutes)

            if not (0 <= hours < 24 and 0 <= minutes < 60):
                raise ValueError("Некорректное время")

            time_str = f"{hours:02d}:{minutes:02d}"

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO tasks (user_id, year, month, day, task, time, created) 
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                           (user_id, year, month, day, task_description, time_str, datetime.now().isoformat()))
            conn.commit()
            conn.close()

            await message.answer(f"✅ Задача добавлена на {day:02d}.{month:02d}.{year}")
            # Показываем обновленный список задач
            await show_day_tasks(message, user_id, year, month, day)

        except ValueError as e:
            await message.answer(f"❌ Ошибка: {str(e)}. Введите время в формате ЧЧ:ММ (например, 14:00)")
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            await message.answer("❌ Ошибка при добавлении задачи")

        # Сбрасываем состояние
        user_state.awaiting_task_text = False


def register_handlers(dp):
    dp.message.register(handle_text_message, F.text)