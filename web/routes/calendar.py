from flask import url_for
from flask_login import login_required, current_user
import calendar
from datetime import datetime
import pytz
from web.config.config import db_connection, MONTH_NAMES
from web.services.category_service import get_user_categories
from flask import current_app as app  # Для доступа к app.logger

def generate_calendar(year, month, user_id, db, highlight_today=True, show_overdue=False):
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    now = datetime.now(pytz.UTC)
    current_day = now.day if (year == now.year and month == now.month) and highlight_today else None

    cursor = db.cursor()

    # Получаем все данные одним запросом
    cursor.execute('''
        WITH task_summary AS (
            SELECT 
                t.day,
                t.id AS task_id,
                t.priority,
                c.color,
                ct.id AS completed_task_id,
                CASE 
                    WHEN ct.id IS NULL 
                    AND (t.year < ? OR (t.year = ? AND t.month < ?) OR (t.year = ? AND t.month = ? AND t.day < ?)) 
                    THEN 1 
                    ELSE 0 
                END AS is_overdue
            FROM tasks t
            LEFT JOIN completed_tasks ct 
                ON t.id = ct.task_id 
                AND ct.user_id = t.user_id
            LEFT JOIN task_categories tc 
                ON t.id = tc.task_id
            LEFT JOIN categories c 
                ON tc.category_id = c.id
            WHERE t.user_id = ? AND t.year = ? AND t.month = ?
        )
        SELECT 
            day,
            COUNT(DISTINCT task_id) AS task_count,
            MAX(priority) AS max_priority,
            GROUP_CONCAT(DISTINCT color) AS colors,
            MAX(is_overdue) AS has_overdue,
            CASE 
                WHEN COUNT(DISTINCT task_id) > 0 
                AND COUNT(DISTINCT task_id) = SUM(CASE WHEN completed_task_id IS NOT NULL THEN 1 ELSE 0 END) 
                THEN 1 
                ELSE 0 
            END AS all_completed
        FROM task_summary
        GROUP BY day
    ''', (
        now.year, now.year, now.month, now.year, now.month, now.day,  # Для is_overdue
        user_id, year, month  # Для фильтрации
    ))

    # Обрабатываем результаты
    days_tasks = {}
    days_colors = {}
    overdue_days = set()
    completed_days = set()

    for row in cursor.fetchall():
        day = row['day']
        days_tasks[day] = {
            'count': row['task_count'],
            'priority': row['max_priority'] or 1  # Если задач нет, используем приоритет по умолчанию
        }
        if row['colors']:
            days_colors[day] = set(row['colors'].split(','))  # Разделяем строку цветов
        if show_overdue and row['has_overdue']:
            overdue_days.add(day)
        if row['all_completed']:
            completed_days.add(day)

    app.logger.debug(f"days_tasks: {days_tasks}")
    app.logger.debug(f"days_colors: {days_colors}")
    app.logger.debug(f"overdue_days: {overdue_days}")
    app.logger.debug(f"completed_days: {completed_days}")

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
            if day in completed_days and day not in overdue_days:
                classes.append('all-tasks-completed')

            app.logger.debug(f"Day {day}: classes = {classes}")

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