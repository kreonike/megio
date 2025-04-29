# bot/handlers/commands.py
from aiogram import types, F
from utils.db import get_user_id_by_telegram_id
from utils.state import user_states, UserState, get_user_state
from config.config import get_db_connection
from datetime import datetime
from keyboards.keyboards import create_calendar_keyboard, create_tasks_keyboard, create_help_keyboard, \
    create_language_keyboard
import logging

logger = logging.getLogger("bot")

async def show_calendar_and_tasks(message: types.Message | types.CallbackQuery, user_id: int, year: int, month: int, day: int):
    telegram_id = message.from_user.id if isinstance(message, types.Message) else message.from_user.id
    user_state = get_user_state(telegram_id)

    if user_state.calendar_message_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id if isinstance(message, types.Message) else message.message.chat.id,
                message_id=user_state.calendar_message_id
            )
        except Exception as e:
            logger.warning(f"Failed to delete old calendar message: {e}")
    if user_state.last_tasks_message_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id if isinstance(message, types.Message) else message.message.chat.id,
                message_id=user_state.last_tasks_message_id
            )
        except Exception as e:
            logger.warning(f"Failed to delete old tasks message: {e}")

    calendar_keyboard = create_calendar_keyboard(year, month, user_id)
    calendar_msg = await (message.answer if isinstance(message, types.Message) else message.message.answer)(
        "📅 Выберите день:",
        reply_markup=calendar_keyboard
    )
    user_state.calendar_message_id = calendar_msg.message_id

    tasks_text, tasks_keyboard = create_tasks_keyboard(user_id, year, month, day)
    tasks_msg = await (message.answer if isinstance(message, types.Message) else message.message.answer)(
        tasks_text,
        reply_markup=tasks_keyboard,
        parse_mode="Markdown"
    )
    user_state.last_tasks_message_id = tasks_msg.message_id

async def cmd_start(message: types.Message):
    telegram_id = message.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)

    response_text = (
        "🔷 <b>Ваш идентификатор:</b>\n\n"
        f"🆔 <b>Telegram ID:</b> <code>{telegram_id}</code>\n"
    )

    if user_id:
        response_text += "ℹ️ Нажмите на  ID, чтобы скопировать"
    else:
        response_text += (
            "\n🔐 <b>Вы не авторизованы</b>\n"
            "Чтобы получить доступ, привяжите этот Telegram ID на сайте\n\n"
            "ℹ️ Нажмите на ID, чтобы скопировать"
        )

    await message.answer(response_text, parse_mode="HTML")

    if user_id:
        now = datetime.now()
        year, month, day = now.year, now.month, now.day
        await show_calendar_and_tasks(message, user_id, year, month, day)
        logger.info(f"Started calendar for telegram_id={telegram_id}, user_id={user_id}")

async def cmd_today(message: types.Message):
    telegram_id = message.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)
    if not user_id:
        await message.answer("🔐 Вы не авторизованы. Привяжите Telegram ID на сайте.")
        logger.warning(f"Unauthorized access attempt by telegram_id={telegram_id}")
        return

    now = datetime.now()
    year, month, day = now.year, now.month, now.day
    await message.answer(f"📅 Задачи на сегодня ({day:02d}.{month:02d}.{year}):", parse_mode="Markdown")
    await show_calendar_and_tasks(message, user_id, year, month, day)
    logger.info(f"Showed today's tasks for telegram_id={telegram_id}")

async def cmd_add(message: types.Message):
    telegram_id = message.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)
    if not user_id:
        await message.answer("🔐 Вы не авторизованы. Привяжите Telegram ID на сайте.")
        logger.warning(f"Unauthorized access attempt by telegram_id={telegram_id}")
        return

    now = datetime.now()
    await message.answer(
        "📅 Чтобы добавить задачу:\n"
        "1. Выберите день в календаре\n"
        "2. Нажмите кнопку '➕ Добавить задачу'\n"
        "3. Введите задачу в формате: ЧЧ:ММ Текст задачи\n\n"
        "Пример: <code>15:00 Встреча с клиентом</code>",
        parse_mode="HTML"
    )
    await show_calendar_and_tasks(message, user_id, now.year, now.month, now.day)

async def cmd_me(message: types.Message):
    telegram_id = message.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)
    if not user_id:
        await message.answer("🔐 Вы не авторизованы. Привяжите Telegram ID на сайте.")
        logger.warning(f"Unauthorized access attempt by telegram_id={telegram_id}")
        return

    from bot.utils.db import get_user_profile
    profile = await get_user_profile(user_id)
    if profile:
        username, email = profile
        await message.answer(f"👤 Ваш профиль:\nИмя: {username}\nEmail: {email}")
        logger.info(f"Showed profile for telegram_id={telegram_id}, user_id={user_id}")
    else:
        await message.answer("❌ Профиль не найден.")
        logger.warning(f"Profile not found for telegram_id={telegram_id}, user_id={user_id}")

    now = datetime.now()
    await show_calendar_and_tasks(message, user_id, now.year, now.month, now.day)

async def cmd_help(message: types.Message):
    telegram_id = message.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)
    if not user_id:
        await message.answer("🔐 Вы не авторизованы. Привяжите Telegram ID на сайте.")
        logger.warning(f"Unauthorized access attempt by telegram_id={telegram_id}")
        return

    help_text = "📚 *Список доступных команд:*"
    help_keyboard = create_help_keyboard(lang="ru")  # Указываем язык
    await message.answer(help_text, reply_markup=help_keyboard, parse_mode="Markdown")
    logger.info(f"Showed help for telegram_id={telegram_id}")

async def handle_help_commands(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)
    if not user_id:
        await callback.answer("🔐 Вы не авторизованы.", show_alert=True)
        logger.warning(f"Unauthorized access attempt by telegram_id={telegram_id}")
        return

    command = callback.data
    now = datetime.now()
    year, month, day = now.year, now.month, now.day

    if command == "cmd_start":
        await show_calendar_and_tasks(callback, user_id, year, month, day)
        logger.info(f"Executed /start from help for telegram_id={telegram_id}")
    elif command == "cmd_today":
        await callback.message.answer(f"📅 Задачи на сегодня ({day:02d}.{month:02d}.{year}):", parse_mode="Markdown")
        await show_calendar_and_tasks(callback, user_id, year, month, day)
        logger.info(f"Executed /today from help for telegram_id={telegram_id}")
    elif command == "cmd_add":
        user_state = get_user_state(telegram_id)
        user_state.awaiting_task_text = True
        await callback.message.answer(
            "📝 Введите задачу в формате: ДД.ММ.ГГГГ ЧЧ:ММ Задача\nПример: 28.03.2025 14:00 Встреча")
        logger.info(f"Executed /add from help for telegram_id={telegram_id}")
    elif command == "cmd_me":
        from bot.utils.db import get_user_profile
        profile = await get_user_profile(user_id)
        if profile:
            username, email = profile
            await callback.message.answer(f"👤 Ваш профиль:\nИмя: {username}\nEmail: {email}")
            logger.info(f"Showed profile for telegram_id={telegram_id}, user_id={user_id}")
        else:
            await callback.message.answer("❌ Профиль не найден.")
            logger.warning(f"Profile not found for telegram_id={telegram_id}, user_id={user_id}")
        await show_calendar_and_tasks(callback, user_id, year, month, day)
    elif command == "cmd_help":
        help_text = "📚 *Список доступных команд:*"
        help_keyboard = create_help_keyboard()
        await callback.message.answer(help_text, reply_markup=help_keyboard, parse_mode="Markdown")
        logger.info(f"Executed /help from help for telegram_id={telegram_id}")

    await callback.answer()

async def handle_back_button(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)
    if not user_id:
        await callback.answer("🔐 Вы не авторизованы.", show_alert=True)
        logger.warning(f"Unauthorized access attempt by telegram_id={telegram_id}")
        return

    _, year, month = callback.data.split("_")
    year, month = int(year), int(month)
    now = datetime.now()
    day = now.day
    await show_calendar_and_tasks(callback, user_id, year, month, day)
    logger.info(f"Handled back button for telegram_id={telegram_id}, showing {year}-{month:02d}-{day:02d}")
    await callback.answer()

async def cmd_cancel(message: types.Message):
    telegram_id = message.from_user.id
    if telegram_id not in user_states:
        user_states[telegram_id] = UserState()
    user_state = user_states[telegram_id]

    if user_state.awaiting_task_text:
        user_state.awaiting_task_text = False
        try:
            if hasattr(user_state, 'add_task_message_id'):
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=user_state.add_task_message_id
                )
        except Exception as e:
            logger.warning(f"Error deleting add task message: {e}")

        await message.answer("❌ Добавление задачи отменено")
        now = datetime.now()
        user_id = await get_user_id_by_telegram_id(telegram_id)
        if user_id:
            await show_calendar_and_tasks(message, user_id, now.year, now.month, now.day)
    else:
        await message.answer("Нечего отменять")

async def cmd_language(message: types.Message):
    telegram_id = message.from_user.id
    user_id = await get_user_id_by_telegram_id(telegram_id)
    if not user_id:
        await message.answer("🔐 Вы не авторизованы. Привяжите Telegram ID на сайте.")
        logger.warning(f"Unauthorized access attempt by telegram_id={telegram_id}")
        return


    keyboard = create_language_keyboard(lang="ru")
    await message.answer("🌍 Выберите язык:", reply_markup=keyboard)
    logger.info(f"Showed language selection for telegram_id={telegram_id}")


def register_handlers(dp):
    dp.message.register(cmd_start, F.text == "/start")
    dp.message.register(cmd_today, F.text == "/today")
    dp.message.register(cmd_add, F.text == "/add")
    dp.message.register(cmd_me, F.text == "/me")
    dp.message.register(cmd_help, F.text == "/help")
    dp.message.register(cmd_language, F.text == "/language")  # Добавляем регистрацию
    dp.callback_query.register(handle_help_commands, F.data.startswith("cmd_"))
    dp.callback_query.register(handle_back_button, F.data.startswith("back_"))
    dp.message.register(cmd_cancel, F.text == "/cancel")