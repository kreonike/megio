# bot/handlers/callbacks.py
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.db import get_user_id_by_telegram_id
from bot.config.config import get_db_connection
from bot.utils.calendar import show_day_tasks
from bot.utils.state import user_states, UserState
from bot.keyboards.keyboards import create_calendar_keyboard, create_delete_tasks_keyboard
from bot.config.constants import MONTH_NAMES
import logging

logger = logging.getLogger("bot")


async def handle_navigation(callback: types.CallbackQuery):
    _, year, month = callback.data.split("_")
    year, month = int(year), int(month)
    telegram_id = callback.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)

    if not user_id:
        logger.warning(f"Unauthorized access attempt by telegram_id={telegram_id}")
        await callback.answer("Ошибка авторизации")
        return

    user_state = user_states.get(telegram_id, UserState())
    day = user_state.current_date[2] if user_state.current_date and user_state.current_date[0] == year and user_state.current_date[1] == month else 1
    logger.info(f"Navigating to {year}-{month:02d}, showing day {day}")
    await show_day_tasks(callback, user_id, year, month, day)
    await callback.answer(f"Переключено на {MONTH_NAMES[month]} {year}")

async def handle_day_selection(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    if telegram_id not in user_states:
        user_states[telegram_id] = UserState()
    user_state = user_states[telegram_id]

    try:
        _, year, month, day = callback.data.split("_")
        year, month, day = int(year), int(month), int(day)
        logger.info(f"Selected date: {year}-{month:02d}-{day:02d}")
        user_state.current_date = (year, month, day)

        user_id = await get_user_id_by_telegram_id(telegram_id)
        if not user_id:
            await callback.answer("🔐 Ошибка авторизации")
            return

        await show_day_tasks(callback, user_id, year, month, day)
        user_state.awaiting_task = True
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in day selection: {e}")
        await callback.answer("Произошла ошибка")

async def handle_task_deletion(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    if len(data_parts) != 2 or not data_parts[1].isdigit():
        await callback.answer("Ошибка: некорректный запрос на удаление", show_alert=True)
        return

    task_id = data_parts[1]
    telegram_id = callback.from_user.id
    user_state = user_states.get(telegram_id, UserState())
    user_id = await get_user_id_by_telegram_id(telegram_id)

    if not user_id:
        await callback.answer("🔐 Ошибка авторизации")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
        conn.commit()
        conn.close()

        await callback.answer("✅ Задача удалена")
        if user_state.current_date:
            year, month, day = user_state.current_date
            await show_day_tasks(callback, user_id, year, month, day)
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        await callback.answer("❌ Ошибка при удалении")
    finally:
        conn.close()

async def handle_add_task(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)

    if not user_id:
        await callback.answer("🔐 Ошибка авторизации", show_alert=True)
        return

    _, _, year, month, day = callback.data.split("_")
    year, month, day = int(year), int(month), int(day)

    user_state = user_states.get(telegram_id, UserState())
    user_state.awaiting_task_text = True
    user_state.current_date = (year, month, day)
    user_states[telegram_id] = user_state

    await callback.message.delete()
    add_task_msg = await callback.message.answer(
        f"✏️ Введите задачу для <b>{day:02d}.{month:02d}.{year}</b> в формате:\n"
        "<b>ЧЧ:ММ Текст задачи</b>\n"
        "Пример: <code>15:00 Встреча с клиентом</code>\n"
        "Или: <code>9 :30 Утренний кофе</code>\n\n"
        "❌ Чтобы отменить, введите /cancel",
        parse_mode="HTML"
    )
    user_state.add_task_message_id = add_task_msg.message_id
    await callback.answer()

async def handle_delete_menu(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)
    if not user_id:
        await callback.answer("🔐 Ошибка авторизации", show_alert=True)
        return

    _, _, year, month, day = callback.data.split("_")
    year, month, day = int(year), int(month), int(day)
    logger.debug(f"Opening delete menu for {year}-{month:02d}-{day:02d}, user_id={user_id}")

    keyboard = create_delete_tasks_keyboard(user_id, year, month, day)
    if not keyboard:
        await callback.answer("Нет задач для удаления", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            f"🗑️ Выберите задачу для удаления на {day:02d}.{month:02d}.{year}:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        await callback.answer("Ошибка при отображении списка задач", show_alert=True)

    await callback.answer()


async def handle_language_change(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)
    if not user_id:
        await callback.answer("🔐 Ошибка авторизации", show_alert=True)
        logger.warning(f"Unauthorized access attempt by telegram_id={telegram_id}")
        return

    lang = callback.data.split("_")[-1]  # "set_lang_ru" -> "ru"
    await callback.message.edit_text(f"✅ Язык изменён на {lang}")
    logger.info(f"Language changed to {lang} for telegram_id={telegram_id}")
    await callback.answer()

def register_handlers(dp):
    dp.callback_query.register(handle_navigation, F.data.startswith("nav_"))
    dp.callback_query.register(handle_day_selection, F.data.startswith("day_"))
    dp.callback_query.register(handle_delete_menu, F.data.startswith("delete_menu_"))
    dp.callback_query.register(handle_task_deletion, F.data.startswith("delete_"))
    dp.callback_query.register(handle_add_task, F.data.startswith("add_task_"))
    dp.callback_query.register(handle_language_change, F.data.startswith("set_lang_"))