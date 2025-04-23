from flask import url_for
from flask_login import login_required, current_user
import calendar
from datetime import datetime
import pytz
from web.config.config import db_connection, MONTH_NAMES
from web.services.category_service import get_user_categories


def generate_calendar(year, month, user_id, db, highlight_today=True, show_overdue=False):
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    now = datetime.now(pytz.UTC)
    current_day = now.day if (year == now.year and month == now.month) and highlight_today else None

    cursor = db.cursor()

    # Получаем количество задач и максимальный приоритет по дням
    cursor.execute('''
        SELECT day, COUNT(*) as task_count, MAX(priority) as max_priority 
        FROM tasks 
        WHERE user_id = ? AND year = ? AND month = ?
        GROUP BY day
    ''', (user_id, year, month))
    days_tasks = {row['day']: {'count': row['task_count'], 'priority': row['max_priority']}
                  for row in cursor.fetchall()}

    # Получаем задачи с категориями
    cursor.execute('''
        SELECT t.day, c.color 
        FROM tasks t
        JOIN task_categories tc ON t.id = tc.task_id
        JOIN categories c ON tc.category_id = c.id
        WHERE t.user_id = ? AND t.year = ? AND t.month = ?
    ''', (user_id, year, month))

    days_colors = {}
    for row in cursor.fetchall():
        day = row['day']
        if day not in days_colors:
            days_colors[day] = set()
        days_colors[day].add(row['color'])

    # Проверяем просроченные задачи
    overdue_days = set()
    if show_overdue:
        cursor.execute('''
            SELECT day 
            FROM tasks 
            WHERE user_id = ? AND year = ? AND month = ?
            AND (year < ? OR (year = ? AND month < ?) OR (year = ? AND month = ? AND day < ?))
        ''', (
            user_id, year, month,
            now.year, now.year, now.month,
            now.year, now.month, now.day
        ))
        overdue_days = {row['day'] for row in cursor.fetchall()}

    # Формируем HTML календаря
    calendar_html = '<table class="calendar-table"><tr>'
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
                <td class={" ".join(classes)} style="{style}">
                    <a href="{url_for("day_tasks", year=year, month=month, day=day)}" class="day-link" data-day="{day}">
                        <span class="day-number">{day}</span>
                        {task_count_html}
                    </a>
                </td>
            '''
        calendar_html += '</tr>'

    calendar_html += '</table>'
    return calendar_html


def calendar_routes(app):
    pass  # Больше нет маршрутов, но функция сохраняется для совместимости