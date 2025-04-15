from datetime import datetime
from flask import jsonify, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from web.config.config import db_connection, MONTH_NAMES
from web.routes.calendar import generate_calendar
from web.services.task_service import add_task, edit_task, delete_task
from web.services.category_service import get_user_categories
from web.utils import json_response, log_task_action, log_error, handle_exceptions

def tasks_routes(app):
    @app.route('/', defaults={'year': None, 'month': None})
    @app.route('/calendar/<int:year>/<int:month>', methods=['GET'])
    @login_required
    def show_calendar(year=None, month=None):
        now = datetime.now()
        if year is None or month is None:
            year = now.year
            month = now.month

        if month > 12:
            month = 1
            year += 1
        elif month < 1:
            month = 12
            year -= 1

        if year < 1900 or year > 9999:
            now = datetime.now()
            return redirect(url_for('show_calendar', year=now.year, month=now.month))

        with db_connection() as db:
            calendar_html = generate_calendar(year, month, current_user.id, db, highlight_today=True, show_overdue=True)
            categories = get_user_categories(db, current_user.id)

        return render_template('calendar.html',
                               calendar=calendar_html,
                               year=year,
                               month=month,
                               russian_month_name=MONTH_NAMES[month],
                               username=current_user.username,
                               categories=categories,
                               current_user_id=current_user.id)

    @app.route('/tasks/<int:year>/<int:month>/<int:day>', methods=['GET', 'POST'])
    @login_required
    def day_tasks(year, month, day):
        with db_connection() as db:
            cursor = db.cursor()
            categories = get_user_categories(db, current_user.id)

            if request.method == 'POST':
                # Внутренняя функция для обработки POST-запроса
                @handle_exceptions
                def process_post():
                    if 'delete' in request.form:
                        task_id = request.form.get('delete')
                        delete_task(db, current_user.id, task_id)
                        log_task_action(app.logger, "deleted", task_id, current_user.id, year, month, day)
                        return True, {'message': 'Задача удалена', 'category': 'success'}

                    elif 'task_id' in request.form:
                        task_id = request.form.get('task_id')
                        task_text = request.form.get('task')
                        time = request.form.get('time')
                        priority = request.form.get('priority', 1, type=int)
                        category_ids = request.form.getlist('categories', type=int)
                        repeat_enabled = 'repeat_enabled' in request.form
                        repeat_days = request.form.get('repeat_days', type=int) if repeat_enabled else None
                        repeat_start = request.form.get('repeat_start') if repeat_enabled else None
                        repeat_end = request.form.get('repeat_end') if repeat_enabled else None

                        if not task_text:
                            raise ValueError('Task cannot be empty')

                        edit_task(
                            db,
                            current_user.id,
                            task_id,
                            task_text,
                            time,
                            priority,
                            category_ids,
                            repeat_days if repeat_enabled and repeat_days and repeat_days > 0 else None,
                            repeat_start if repeat_enabled and repeat_days and repeat_days > 0 else None,
                            repeat_end if repeat_enabled and repeat_days and repeat_days > 0 else None
                        )
                        log_task_action(app.logger, "updated", task_id, current_user.id, year, month, day)
                        return True, {'message': 'Задача обновлена', 'category': 'success'}

                    elif 'task' in request.form:
                        task_text = request.form.get('task')
                        time = request.form.get('time')
                        priority = request.form.get('priority', 1, type=int)
                        category_ids = request.form.getlist('categories', type=int)
                        repeat_enabled = 'repeat_enabled' in request.form
                        repeat_days = request.form.get('repeat_days', type=int) if repeat_enabled else None
                        repeat_start = request.form.get('repeat_start') if repeat_enabled else None
                        repeat_end = request.form.get('repeat_end') if repeat_enabled else None

                        if not task_text:
                            raise ValueError('Task cannot be empty')

                        task_id = add_task(
                            db,
                            current_user.id,
                            year,
                            month,
                            day,
                            task_text,
                            time,
                            priority,
                            category_ids,
                            repeat_days if repeat_enabled and repeat_days and repeat_days > 0 else None,
                            repeat_start if repeat_enabled and repeat_days and repeat_days > 0 else None,
                            repeat_end if repeat_enabled and repeat_days and repeat_days > 0 else None
                        )
                        log_task_action(app.logger, "added", task_id, current_user.id, year, month, day)
                        return True, {'message': 'Задача добавлена', 'category': 'success', 'task_id': task_id}

                try:
                    success, flash_data = process_post()
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return json_response(True, data={'task_id': flash_data.get('task_id')})
                    flash(flash_data['message'], flash_data['category'])
                    return redirect(url_for('day_tasks', year=year, month=month, day=day))
                except ValueError as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return json_response(False, error=str(e), status_code=400)
                    flash(str(e), 'error')
                    return redirect(url_for('day_tasks', year=year, month=month, day=day))

            cursor.execute('''
                SELECT 
                    t.id, t.task, t.time, t.created, t.repeat_days, t.repeat_start, t.repeat_end, t.priority,
                    CASE WHEN ct.id IS NOT NULL THEN 1 ELSE 0 END as completed,
                    GROUP_CONCAT(tc.category_id) AS category_ids
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
                try:
                    task['category_ids'] = list(map(int, task['category_ids'].split(','))) if task['category_ids'] else []
                except (ValueError, TypeError):
                    task['category_ids'] = []
                tasks.append(task)

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
    def month_tasks(year, month):
        with db_connection() as db:
            cursor = db.cursor()

            cursor.execute('''
                SELECT 
                    t.day, t.id, t.task, t.priority, t.time,
                    t.repeat_days, t.repeat_start, t.repeat_end,
                    CASE WHEN ct.id IS NOT NULL THEN 1 ELSE 0 END as completed,
                    GROUP_CONCAT(tc.category_id) AS category_ids
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
                    'category_ids': [int(cid) for cid in row['category_ids'].split(',')] if row['category_ids'] else []
                }
                tasks_by_day[day].append(task)

            import calendar
            cal = calendar.Calendar()
            month_days = cal.itermonthdays(year, month)
            for day in month_days:
                if day != 0 and day not in tasks_by_day:
                    tasks_by_day[day] = []

            return json_response(True, data={'tasksByDay': tasks_by_day})