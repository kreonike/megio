from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import calendar
from datetime import datetime
from bot.config.config import get_db_connection
from bot.locales.loader import i18n
import logging

logger = logging.getLogger("bot")

def create_calendar_keyboard(year: int, month: int, user_id: int, lang: str = None) -> InlineKeyboardMarkup:
    if lang is None:
        logger.warning("Language is None, defaulting to 'ru'")
        lang = "ru"

    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    now = datetime.now()
    current_day = now.day if year == now.year and month == now.month else None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT day, COUNT(*) FROM tasks 
                      WHERE user_id = ? AND year = ? AND month = ?
                      GROUP BY day''', (user_id, year, month))
    days_tasks = dict(cursor.fetchall())
    conn.close()

    keyboard = []
    prev_month, prev_year = (month - 1, year) if month > 1 else (12, year - 1)
    next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)

    keyboard.append([
        InlineKeyboardButton(
            text=i18n.get("buttons.calendar.prev_month", lang=lang),
            callback_data=f"nav_{prev_year}_{prev_month}"
        ),
        InlineKeyboardButton(
            text=f"{i18n.get(f'buttons.months.{month}', lang=lang)} {year}",
            callback_data="ignore"
        ),
        InlineKeyboardButton(
            text=i18n.get("buttons.calendar.next_month", lang=lang),
            callback_data=f"nav_{next_year}_{next_month}"
        )
    ])

    weekdays = i18n.get("buttons.weekdays.short", lang=lang)  # Исправляем ключ
    if not isinstance(weekdays, list):
        logger.error(f"i18n.get('buttons.weekdays.short', lang={lang}) returned {weekdays}, using fallback")
        weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    logger.info(f"Weekdays used: {weekdays}")
    keyboard.append([
        InlineKeyboardButton(text=day, callback_data="ignore")
        for day in weekdays
    ])

    for week in month_days:
        week_buttons = []
        for day in week:
            if day == 0:
                week_buttons.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
                continue
            has_tasks = day in days_tasks and days_tasks[day] > 0
            button_text = f"🟢{day}" if day == current_day else f"🔵{day}" if has_tasks else str(day)
            week_buttons.append(InlineKeyboardButton(
                text=button_text,
                callback_data=f"day_{year}_{month}_{day}"
            ))
        keyboard.append(week_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_tasks_keyboard(user_id: int, year: int, month: int, day: int, lang: str = None) -> tuple[
    str, InlineKeyboardMarkup]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT id, task, time FROM tasks 
                      WHERE user_id = ? AND year = ? AND month = ? AND day = ?
                      ORDER BY time, created''', (user_id, year, month, day))
    tasks = cursor.fetchall()
    conn.close()

    date_str = f"{day:02d}.{month:02d}.{year}"
    tasks_text = i18n.get("messages.tasks.day_header", lang=lang).replace('*', '').format(date=date_str)

    keyboard = []

    # Кнопка "Добавить задачу" (шириной как 7 кнопок календаря)
    add_task_button = InlineKeyboardButton(
        text=f"➕               {i18n.get('buttons.add_task', lang=lang)}               ➕",
        callback_data=f"add_task_{year}_{month}_{day}"
    )
    keyboard.append([add_task_button])  # Растягивается на всю строку

    if not tasks:
        tasks_text += i18n.get("messages.tasks.no_tasks", lang=lang)
    else:
        for task_id, task_text, task_time in tasks:
            time_prefix_template = i18n.get("messages.tasks.time_prefix", lang=lang)
            time_str = time_prefix_template.format(time=task_time) if task_time else ""

            task_text = task_text.translate(str.maketrans({
                '*': '\\*',
                '_': '\\_',
                '`': '\\`',
                '[': '\\[',
                ']': '\\]',
                '(': '\\(',
                ')': '\\)'
            }))

            tasks_text += f"\n• {time_str}{task_text}"

        # Кнопка "Удалить задачу" (шириной как 7 кнопок календаря)
        delete_task_button = InlineKeyboardButton(
            text=f"❌                    {i18n.get('buttons.delete_task', lang=lang)}               ❌",
            callback_data=f"delete_menu_{year}_{month}_{day}"
        )
        keyboard.append([delete_task_button])

    # Кнопка "Назад" (шириной как 7 кнопок календаря)
    back_button = InlineKeyboardButton(
        text=f"          {i18n.get('buttons.back', lang=lang)}          ",
        callback_data=f"back_{year}_{month}"
    )
    keyboard.append([back_button])

    return tasks_text, InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_delete_tasks_keyboard(user_id: int, year: int, month: int, day: int, lang: str = None) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для удаления задач."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT id, task, time FROM tasks 
                      WHERE user_id = ? AND year = ? AND month = ? AND day = ?
                      ORDER BY time, created''', (user_id, year, month, day))
    tasks = cursor.fetchall()
    conn.close()

    if not tasks:
        return None

    keyboard = []
    for task_id, task_text, task_time in tasks:
        print(f"Debug - task_time: {task_time}")
        time_str = f"{i18n.get('tasks.time_prefix', time=task_time, lang=lang)}" if task_time else ""
        button_text = f"❌ {time_str}{task_text[:20]}..." if len(task_text) > 20 else f"❌ {time_str}{task_text}"
        keyboard.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"delete_{task_id}"
        )])

    keyboard.append([
        InlineKeyboardButton(
            text=i18n.get("buttons.cancel", lang=lang),
            callback_data=f"back_{year}_{month}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def create_help_keyboard(lang: str = None) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для команды /help."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=i18n.get("messages.help.commands.start", lang=lang),
            callback_data="cmd_start"
        )],
        [InlineKeyboardButton(
            text=i18n.get("messages.help.commands.today", lang=lang),
            callback_data="cmd_today"
        )],
        [InlineKeyboardButton(
            text=i18n.get("messages.help.commands.add", lang=lang),
            callback_data="cmd_add"
        )],
        [InlineKeyboardButton(
            text=i18n.get("messages.help.commands.me", lang=lang),
            callback_data="cmd_me"
        )],
        [InlineKeyboardButton(
            text=i18n.get("messages.help.commands.help", lang=lang),
            callback_data="cmd_help"
        )]
    ])

def create_language_keyboard(lang: str = None) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора языка."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=i18n.get("language.russian", lang=lang),
                callback_data="set_lang_ru"
            ),
            InlineKeyboardButton(
                text=i18n.get("language.english", lang=lang),
                callback_data="set_lang_en"
            )
        ],
        [
            InlineKeyboardButton(
                text=i18n.get("buttons.cancel", lang=lang),
                callback_data="cancel_language"
            )
        ]
    ])

def create_main_menu_keyboard(lang: str = None) -> InlineKeyboardMarkup:
    """Создаёт основную меню-клавиатуру."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=i18n.get("menu.calendar", lang=lang),
                callback_data="open_calendar"
            )
        ],
        [
            InlineKeyboardButton(
                text=i18n.get("menu.language", lang=lang),
                callback_data="change_language"
            ),
            InlineKeyboardButton(
                text=i18n.get("menu.help", lang=lang),
                callback_data="cmd_help"
            )
        ]
    ])