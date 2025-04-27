# web/routes/calendar.py
from datetime import datetime, timedelta
from flask import url_for
from flask_login import login_required, current_user
import calendar
import pytz
from web.config.config import db_connection, MONTH_NAMES
from web.services.category_service import get_user_categories
from flask import current_app as app


def generate_calendar(year, month, user_id, db, highlight_today=True, show_overdue=False):
    """
    Генерирует HTML-календарь для указанного года и месяца с задачами пользователя.

    Args:
        year: Год календаря.
        month: Месяц календаря.
        user_id: ID пользователя.
        db: Соединение с базой данных.
        highlight_today: Подсвечивать текущий день (по умолчанию True).
        show_overdue: Показывать просроченные задачи (по умолчанию False).

    Returns:
        HTML-строка с таблицей календаря.
    """
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    now = datetime.now(pytz.UTC)
    current_day = now.day if (year == now.year and month == now.month) and highlight_today else None

    cursor = db.cursor()

    # Получаем задачи пользователя только для указанного года и месяца
    cursor.execute('''
        SELECT 
            t.id AS task_id,
            t.year,
            t.month,
            t.day,
            t.priority,
            t.repeat_days,
            t.repeat_start,
            t.repeat_end,
            c.color,
            ct.id AS completed_task_id
        FROM tasks t
        LEFT JOIN completed_tasks ct 
            ON t.id = ct.task_id 
            AND ct.user_id = t.user_id
        LEFT JOIN task_categories tc 
            ON t.id = tc.task_id
        LEFT JOIN categories c 
            ON tc.category_id = c.id
        WHERE t.user_id = ? AND (t.year = ? AND t.month = ? OR t.repeat_days IS NOT NULL)
    ''', (user_id, year, month))

    # Обрабатываем задачи и создаём виртуальные экземпляры для повторяющихся задач
    days_tasks = {}
    days_colors = {}
    overdue_days = set()
    completed_days = set()

    for row in cursor.fetchall():
        task_id = row['task_id']
        task_year = row['year']
        task_month = row['month']
        task_day = row['day']
        priority = row['priority']
        repeat_days = row['repeat_days']
        repeat_start = row['repeat_start']
        repeat_end = row['repeat_end']
        color = row['color']
        completed_task_id = row['completed_task_id']

        # Функция для добавления задачи в день
        def add_task_to_day(day, is_overdue=False):
            if day not in days_tasks:
                days_tasks[day] = {'count': 0, 'priority': 1}
                days_colors[day] = set()
            days_tasks[day]['count'] += 1
            days_tasks[day]['priority'] = max(days_tasks[day]['priority'], priority or 1)
            if color:
                days_colors[day].add(color)
            if is_overdue and show_overdue:
                overdue_days.add(day)
            if completed_task_id:
                completed_days.add(day)

        # Обрабатываем основную задачу, только если она принадлежит текущему месяцу
        if task_year == year and task_month == month:
            is_overdue = (not completed_task_id and
                          (task_year < now.year or
                           (task_year == now.year and task_month < now.month) or
                           (task_year == now.year and task_month == now.month and task_day < now.day)))
            add_task_to_day(task_day, is_overdue)
            app.logger.debug(f"Добавлена основная задача {task_id} для {year}-{month}-{task_day}")

        # Обрабатываем повторяющиеся задачи, только если все поля заполнены
        if repeat_days and repeat_start and repeat_end:
            try:
                start_date = datetime.strptime(repeat_start, '%Y-%m-%d')
                end_date = datetime.strptime(repeat_end, '%Y-%m-%d')
                if start_date > end_date or repeat_days <= 0:
                    app.logger.warning(f"Некорректные параметры повторения для задачи {task_id}")
                    continue
                current_date = start_date
                while current_date <= end_date:
                    if current_date.year == year and current_date.month == month:
                        is_overdue = (not completed_task_id and current_date < now)
                        add_task_to_day(current_date.day, is_overdue)
                        app.logger.debug(f"Добавлена повторяющаяся задача {task_id} для {year}-{month}-{current_date.day}")
                    current_date += timedelta(days=repeat_days)
            except ValueError as e:
                app.logger.error(f"Некорректный формат даты для задачи {task_id}: {e}")

    app.logger.debug(f"days_tasks: {days_tasks}")
    app.logger.debug(f"days_colors: {days_colors}")
    app.logger.debug(f"overdue_days: {overdue_days}")
    app.logger.debug(f"completed_days: {completed_days}")

    # Формируем HTML календаря
    calendar_html = f'<table class="calendar-table" data-year="{year}" data-month="{month}"><tr>'
    calendar_html += ''.join(f'<th>{day}</th>' for day in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'])
    calendar_html += '</tr>'

    for week in month_days:
        calendar_html += '<tr>'
        for i, day in enumerate(week):
            if day == 0:
                calendar_html += '<td class="empty-day"></td>'
                continue

            classes = ['day-cell']
            if day == current_day:
                classes.append('today')
            if day in days_tasks:
                classes.append('has-tasks')
            if i >= 5:
                classes.append('weekend')
            if day in overdue_days:
                classes.append('has-overdue-tasks')
            if day in completed_days and day not in overdue_days:
                classes.append('all-tasks-completed')

            app.logger.debug(f"День {day}: классы = {classes}")

            style = ''
            if day in days_colors:
                colors = days_colors[day]
                if len(colors) == 1:
                    style = f"background-color: {next(iter(colors))}20;"
                else:
                    gradient = ','.join([f"{color} 0%, {color} 50%" for color in colors])
                    style = f"background: linear-gradient(135deg, {gradient});"

            task_info = days_tasks.get(day, {})
            task_count = task_info.get('count', 0)
            priority = task_info.get('priority', 1)

            priority_class = {
                3: 'priority-high',
                2: 'priority-medium',
                1: 'priority-low'
            }.get(priority, 'priority-low')

            task_count_html = f'<span class="task-count-badge {priority_class}">{task_count}</span>' if task_count > 0 else ''

            calendar_html += f'''
                <td class="{" ".join(classes)}" style="{style}">
                    <a href="{url_for("day_tasks", year=year, month=month, day=day)}" class="day-link" data-day="{day}">
                        <span class="day-number">{day}</span>
                        {task_count_html}
                    </a>
                </td>
            '''
        calendar_html += '</tr>'

    calendar_html += '</table>'
    return calendar_html