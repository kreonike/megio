from datetime import datetime
from flask import jsonify, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from web.config.config import db_connection, MONTH_NAMES
from web.routes.calendar import generate_calendar
from web.services.task_service import add_task, edit_task, delete_task
from web.services.category_service import get_user_categories, get_default_categories, parse_category_ids
from web.utils import json_response, log_action, log_error, handle_exceptions, validate_date, handle_crud_post
import calendar

def tasks_routes(app):
    @app.route('/', defaults={'year': None, 'month': None})
    @app.route('/calendar/<int:year>/<int:month>', methods=['GET'])
    @login_required
    def show_calendar(year=None, month=None):
        now = datetime.now()
        if year is None or month is None:
            year = now.year
            month = now.month

        year, month, _ = validate_date(year, month, 1, redirect_endpoint='show_calendar')

        with db_connection() as db:
            calendar_html = generate_calendar(year, month, current_user.id, db, highlight_today=True, show_overdue=True)
            categories = get_default_categories(db, current_user.id)

        return render_template('calendar.html',
                               calendar=calendar_html,
                               year=year,
                               month=month,
                               russian_month_name=MONTH_NAMES[month],
                               username=current_user.username,
                               categories=categories,
                               current_user_id=current_user.id)

    def handle_delete(db, year, month, day):
        task_id = request.form.get('delete')
        if not task_id:
            raise ValueError('Идентификатор задачи обязателен')
        delete_task(db, current_user.id, task_id)
        log_action(app.logger, "Task", "deleted", current_user.id, entity_id=task_id,
                   extra_info={'date': {'year': year, 'month': month, 'day': day}})
        return True, {'message': 'Задача удалена', 'category': 'success'}

    def handle_update(db, year, month, day):
        task_id = request.form.get('task_id')
        task_text = request.form.get('task')
        time = request.form.get('time')
        priority = request.form.get('priority', 1, type=int)
        category_ids = request.form.getlist('categories', type=int)
        repeat_enabled = 'repeat_enabled' in request.form
        repeat_days = request.form.get('repeat_days', type=int) if repeat_enabled else None
        repeat_start = request.form.get('repeat_start') if repeat_enabled else None
        repeat_end = request.form.get('repeat_end') if repeat_enabled else None
        if not task_id:
            raise ValueError('Идентификатор задачи обязателен')
        if not task_text:
            raise ValueError('Задача не может быть пустой')
        edit_task(
            db,
            current_user.id,
            task_id,
            task_text,
            time,
            priority,
            category_ids or [],  # Убедимся, что category_ids всегда список
            repeat_days if repeat_enabled and repeat_days and repeat_days > 0 else None,
            repeat_start if repeat_enabled and repeat_days and repeat_days > 0 else None,
            repeat_end if repeat_enabled and repeat_days and repeat_days > 0 else None
        )
        log_action(app.logger, "Task", "updated", current_user.id, entity_id=task_id,
                   extra_info={'date': {'year': year, 'month': month, 'day': day}})
        return True, {'message': 'Задача обновлена', 'category': 'success'}

    def handle_add(db, year, month, day):
        task_text = request.form.get('task')
        time = request.form.get('time')
        priority = request.form.get('priority', 1, type=int)
        category_ids = request.form.getlist('categories', type=int)
        repeat_enabled = 'repeat_enabled' in request.form
        repeat_days = request.form.get('repeat_days', type=int) if repeat_enabled else None
        repeat_start = request.form.get('repeat_start') if repeat_enabled else None
        repeat_end = request.form.get('repeat_end') if repeat_enabled else None
        if not task_text:
            raise ValueError('Задача не может быть пустой')
        task_id = add_task(
            db,
            current_user.id,
            year,
            month,
            day,
            task_text,
            time,
            priority,
            category_ids or [],  # Убедимся, что category_ids всегда список
            repeat_days if repeat_enabled and repeat_days and repeat_days > 0 else None,
            repeat_start if repeat_enabled and repeat_days and repeat_days > 0 else None,
            repeat_end if repeat_enabled and repeat_days and repeat_days > 0 else None
        )
        log_action(app.logger, "Task", "added", current_user.id, entity_id=task_id,
                   extra_info={'date': {'year': year, 'month': month, 'day': day}})
        return True, {'message': 'Задача добавлена', 'category': 'success', 'task_id': task_id}

    @app.route('/tasks/<int:year>/<int:month>/<int:day>', methods=['GET', 'POST'])
    @login_required
    def day_tasks(year, month, day):
        year, month, day = validate_date(year, month, day, redirect_endpoint='show_calendar')
        with db_connection() as db:
            if request.method == 'POST':
                @handle_crud_post(
                    action_handlers=lambda year, month, day: {
                        'delete': lambda: handle_delete(db, year, month, day),
                        'update': lambda: handle_update(db, year, month, day),
                        'add': lambda: handle_add(db, year, month, day)
                    },
                    redirect_endpoint='day_tasks',
                    ajax_response_data=lambda flash_data: {'task_id': flash_data.get('task_id')} if isinstance(flash_data, dict) and flash_data.get('task_id') else {}
                )
                def process_post():
                    pass
                return process_post(year=year, month=month, day=day)

            cursor = db.cursor()
            categories = get_default_categories(db, current_user.id)

            cursor.execute('''
                SELECT 
                    t.id, t.task, t.time, t.created, t.repeat_days, t.repeat_start, t.repeat_end, t.priority,
                    CASE WHEN ct.id IS NOT NULL THEN 1 ELSE 0 END as completed,
                    COALESCE(GROUP_CONCAT(tc.category_id), '') AS category_ids
                FROM tasks t
                LEFT JOIN completed_tasks ct 
                    ON t.id = ct.task_id 
                    AND ct.user_id = t.user_id
                LEFT JOIN task_categories tc ON t.id = tc.task_id
                WHERE t.user_id = ? AND t.year = ? AND t.month = ? AND t.day = ?
                GROUP BY t.id
                ORDER BY t.priority DESC, t.time, t.created
            ''', (current_user.id, year, month, day))
            tasks = []
            for row in cursor.fetchall():
                task = dict(row)
                task['category_ids'] = parse_category_ids(task['category_ids']) if task['category_ids'] else []
                tasks.append(task)
            log_action(app.logger, "Tasks", "fetched_day", current_user.id,
                       extra_info={'year': year, 'month': month, 'day': day, 'task_count': len(tasks)})

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return json_response(True, data={
                    'tasks': tasks,
                    'date': f"{year}-{month:02d}-{day:02d}",
                    'categories': categories
                })

            date_str = f"{day:02d}.{month:02d}.{year}"
            return render_template('tasks.html',
                                   year=year,
                                   month=month,
                                   day=day,
                                   date_str=date_str,
                                   tasks=tasks,
                                   categories=categories)

    @app.route('/tasks/<int:year>/<int:month>', methods=['GET'])
    @login_required
    @handle_exceptions
    def month_tasks(year, month):
        year, month, _ = validate_date(year, month, 1, redirect_endpoint='show_calendar')
        with db_connection() as db:
            cursor = db.cursor()

            cursor.execute('''
                SELECT 
                    t.day, t.id, t.task, t.priority, t.time,
                    t.repeat_days, t.repeat_start, t.repeat_end,
                    CASE WHEN ct.id IS NOT NULL THEN 1 ELSE 0 END as completed,
                    COALESCE(GROUP_CONCAT(tc.category_id), '') AS category_ids
                FROM tasks t
                LEFT JOIN completed_tasks ct 
                    ON t.id = ct.task_id 
                    AND ct.user_id = t.user_id
                LEFT JOIN task_categories tc ON t.id = tc.task_id
                WHERE t.user_id = ? AND t.year = ? AND t.month = ?
                GROUP BY t.id
                ORDER BY t.day
            ''', (current_user.id, year, month))

            tasks_by_day = {}
            for row in cursor.fetchall():
                day = row['day']
                if day not in tasks_by_day:
                    tasks_by_day[day] = []
                task = {
                    'id': row['id'],
                    'task': row['task'],
                    'priority': row['priority'],
                    'time': row['time'],
                    'repeat_days': row['repeat_days'],
                    'repeat_start': row['repeat_start'],
                    'repeat_end': row['repeat_end'],
                    'completed': row['completed'],
                    'category_ids': parse_category_ids(row['category_ids']) if row['category_ids'] else []
                }
                tasks_by_day[day].append(task)

            cal = calendar.Calendar()
            month_days = cal.itermonthdays(year, month)
            for day in month_days:
                if day != 0 and day not in tasks_by_day:
                    tasks_by_day[day] = []

            log_action(app.logger, "Tasks", "fetched_month", current_user.id,
                       extra_info={'year': year, 'month': month,
                                   'task_count': sum(len(tasks) for tasks in tasks_by_day.values())})
            return json_response(True, data={'tasksByDay': tasks_by_day})