# bot/utils/calendar.py
from aiogram import types
from keyboards.keyboards import create_calendar_keyboard, create_tasks_keyboard
import logging

logger = logging.getLogger("bot")

MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

async def show_day_tasks(message: types.Message | types.CallbackQuery, user_id: int, year: int, month: int, day: int):
    logger.info(f"Showing tasks for user_id={user_id}, date={year}-{month:02d}-{day:02d}")

    tasks_text, tasks_keyboard = create_tasks_keyboard(user_id, year, month, day)
    calendar_keyboard = create_calendar_keyboard(year, month, user_id)
    calendar_text = f"📅 *Календарь на {MONTH_NAMES[month]} {year}*"

    try:
        if isinstance(message, types.CallbackQuery):
            await message.message.delete()
            calendar_message = await message.message.answer(
                calendar_text,
                reply_markup=calendar_keyboard,
                parse_mode="HTML"
            )
            tasks_message = await message.message.answer(
                tasks_text,
                reply_markup=tasks_keyboard,
                parse_mode="HTML"
            )
            logger.info(f"Sent calendar message with message_id={calendar_message.message_id}")
            logger.info(f"Sent tasks message with message_id={tasks_message.message_id}")
            await message.answer()
        else:
            calendar_message = await message.answer(
                calendar_text,
                reply_markup=calendar_keyboard,
                parse_mode="HTML"
            )
            tasks_message = await message.answer(
                tasks_text,
                reply_markup=tasks_keyboard,
                parse_mode="HTML"
            )
            logger.info(f"Sent calendar message with message_id={calendar_message.message_id}")
            logger.info(f"Sent tasks message with message_id={tasks_message.message_id}")
    except Exception as e:
        logger.error(f"Error updating messages: {e}")
        await message.answer("Произошла ошибка при обновлении календаря и задач")