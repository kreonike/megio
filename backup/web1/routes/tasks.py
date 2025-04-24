from datetime import datetime

from flask import jsonify, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from web.config.config import get_db, MONTH_NAMES
from web.routes.calendar import generate_calendar

def tasks_routes(app, get_db):
    @app.route('/')
    @login_required
    def show_calendar():
        now = datetime.now()
        year = request.args.get('year', default=now.year, type=int)
        month = request.args.get('month', default=now.month, type=int)

        if month > 12:
            month = 1
            year += 1
        elif month < 1:
            month = 12
            year -= 1

        # Получаем категории пользователя
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, name, color FROM categories WHERE user_id = ?', (current_user.id,))
        categories = cursor.fetchall()

        calendar_html = generate_calendar(year, month, current_user.id, get_db)
        return render_template('calendar.html',
                              calendar=calendar_html,
                              year=year,
                              month=month,
                              russian_month_name=MONTH_NAMES[month],
                              username=current_user.username,
                              categories=categories)

    @app.route('/tasks/<int:year>/<int:month>/<int:day>', methods=['GET', 'POST'])
    @login_required
    def day_tasks(year, month, day):
        app.logger.info(f"Received task form data: {request.form}")
        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute('SELECT id, name, color FROM categories WHERE user_id = ?', (current_user.id,))
            categories = cursor.fetchall()

            if request.method == 'POST':
                # Удаление задачи
                if 'delete' in request.form:
                    task_id = request.form.get('delete')
                    cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, current_user.id))
                    cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
                    db.commit()
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({'status': 'success'})
                    flash('Задача удалена', 'success')

                # Редактирование задачи
                elif 'task_id' in request.form:
                    task_id = request.form.get('task_id')
                    new_task = request.form.get('task')
                    new_time = request.form.get('time')
                    priority = request.form.get('priority', 1)
                    category_ids = request.form.getlist('categories')
                    repeat_enabled = 'repeat_enabled' in request.form
                    repeat_days = request.form.get('repeat_days') if repeat_enabled else None
                    repeat_start = request.form.get('repeat_start') if repeat_enabled else None
                    repeat_end = request.form.get('repeat_end') if repeat_enabled else None

                    if new_task:
                        cursor.execute('''
                            UPDATE tasks 
                            SET task = ?, time = ?, 
                                repeat_days = ?, 
                                repeat_start = ?, 
                                repeat_end = ?,
                                priority = ?
                            WHERE id = ? AND user_id = ?
                        ''', (
                            new_task,
                            new_time,
                            int(repeat_days) if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
                            repeat_start if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
                            repeat_end if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
                            priority,
                            task_id,
                            current_user.id
                        ))

                        cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
                        for cat_id in category_ids:
                            cursor.execute('INSERT INTO task_categories (task_id, category_id) VALUES (?, ?)',
                                           (task_id, cat_id))

                        db.commit()
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return jsonify({'status': 'success'})
                        flash('Задача обновлена', 'success')

                # Добавление новой задачи
                elif 'task' in request.form and 'date' in request.form:
                    task_text = request.form.get('task')
                    task_time = request.form.get('time')
                    priority = request.form.get('priority', 1)
                    category_ids = request.form.getlist('categories')
                    repeat_enabled = 'repeat_enabled' in request.form
                    repeat_days = request.form.get('repeat_days') if repeat_enabled else None
                    repeat_start = request.form.get('repeat_start') if repeat_enabled else None
                    repeat_end = request.form.get('repeat_end') if repeat_enabled else None
                    date = request.form.get('date')
                    date_parts = date.split('-')
                    year, month, day = map(int, date_parts)

                    if task_text:
                        cursor.execute('''
                            INSERT INTO tasks (user_id, year, month, day, task, time, repeat_days, repeat_start, repeat_end, priority)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            current_user.id,
                            year,
                            month,
                            day,
                            task_text,
                            task_time,
                            int(repeat_days) if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
                            repeat_start if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
                            repeat_end if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
                            priority
                        ))

                        task_id = cursor.lastrowid
                        for cat_id in category_ids:
                            cursor.execute('INSERT INTO task_categories (task_id, category_id) VALUES (?, ?)',
                                           (task_id, cat_id))

                        db.commit()
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return jsonify({'status': 'success', 'task_id': task_id})
                        flash('Задача добавлена', 'success')

                if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
                    return redirect(url_for('day_tasks', year=year, month=month, day=day))

            # GET-запрос
            cursor.execute('''
                SELECT t.id, t.task, t.time, t.created, t.repeat_days, t.repeat_start, t.repeat_end, t.priority,
                       GROUP_CONCAT(tc.category_id) AS category_ids
                FROM tasks t
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
                except (ValueError, TypeError) as e:
                    app.logger.error(f"Error processing category_ids for task {task['id']}: {e}")
                    task['category_ids'] = []
                tasks.append(task)
            app.logger.info(f"Tasks data for day {year}-{month}-{day}: {tasks}")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'tasks': tasks, 'date': f"{year}-{month:02d}-{day:02d}", 'categories': [dict(cat) for cat in categories]})

            date_str = f"{day:02d}.{month:02d}.{year}"
            return render_template('tasks.html', year=year, month=month, day=day, date_str=date_str,
                                   tasks=tasks, categories=categories)

        except Exception as e:
            app.logger.error(f"Error in day_tasks: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @app.route('/tasks/<int:year>/<int:month>', methods=['GET'])
    @login_required
    def month_tasks(year, month):
        db = get_db()
        cursor = db.cursor()

        # Получаем задачи по дням месяца
        cursor.execute('''
            SELECT day, task, priority 
            FROM tasks 
            WHERE user_id = ? AND year = ? AND month = ?
            ORDER BY day
        ''', (current_user.id, year, month))

        tasks_by_day = {}
        for row in cursor.fetchall():
            day = row['day']
            if day not in tasks_by_day:
                tasks_by_day[day] = []
            tasks_by_day[day].append({
                'task': row['task'],
                'priority': row['priority']
            })

        # Добавляем все дни месяца, даже если задач нет
        import calendar
        cal = calendar.Calendar()
        month_days = cal.itermonthdays(year, month)
        for day in month_days:
            if day != 0 and day not in tasks_by_day:
                tasks_by_day[day] = []

        return jsonify({'tasksByDay': tasks_by_day})