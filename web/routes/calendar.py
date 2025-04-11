# web/routes/calendar.py
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
import calendar
from datetime import datetime
import pytz
import json

def generate_calendar(year, month, user_id, get_db):
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)
    now = datetime.now(pytz.UTC)
    current_day = now.day if (year == now.year and month == now.month) else None

    db = get_db()
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

    # Начинаем формировать HTML календаря
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

            # Добавляем стили для категорий
            style = ''
            if day in days_colors:
                colors = days_colors[day]
                if len(colors) == 1:
                    style = f"background-color: {next(iter(colors))}20;"  # 20 - прозрачность
                else:
                    gradient = ','.join([f"{color} 0%, {color} 50%" for color in colors])
                    style = f"background: linear-gradient(135deg, {gradient});"

            task_info = days_tasks.get(day, {})
            task_count = task_info.get('count', 0)
            priority = task_info.get('priority', 1)

            priority_class = ''
            if priority == 3:
                priority_class = 'priority-high'
            elif priority == 2:
                priority_class = 'priority-medium'
            else:
                priority_class = 'priority-low'

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

def calendar_routes(app, get_db):
    # Список русских названий месяцев
    RUSSIAN_MONTHS = [
        "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]

    @app.route('/calendar/<int:year>/<int:month>', methods=['GET'])
    @login_required
    def show_calendar(year=None, month=None):
        # Если год и месяц не указаны, используем текущие
        if year is None or month is None:
            now = datetime.now(pytz.UTC)
            year = now.year
            month = now.month

        # Проверка корректности года и месяца
        if month < 1 or month > 12:
            flash('Некорректный месяц', 'error')
            return redirect(url_for('show_calendar', year=datetime.now().year, month=datetime.now().month))
        if year < 1900 or year > 9999:
            flash('Некорректный год', 'error')
            return redirect(url_for('show_calendar', year=datetime.now().year, month=datetime.now().month))

        # Получаем календарь на указанный месяц
        cal = calendar.monthcalendar(year, month)
        today = datetime.now(pytz.UTC)
        today_year, today_month, today_day = today.year, today.month, today.day

        # Генерируем HTML-код календаря
        calendar_html = '<table class="calendar-table"><thead><tr>'
        for day_name in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']:
            calendar_html += f'<th>{day_name}</th>'
        calendar_html += '</tr></thead><tbody>'

        for week in cal:
            calendar_html += '<tr>'
            for i, day in enumerate(week):
                if day == 0:
                    calendar_html += '<td class="day-cell empty"></td>'
                    continue

                # Проверяем, является ли день выходным
                is_weekend = i >= 5  # Суббота или воскресенье
                is_today = (year == today_year and month == today_month and day == today_day)

                # Получаем задачи для этого дня
                db = get_db()
                cursor = db.cursor()
                cursor.execute('''
                    SELECT id, task, time, priority, google_event_id 
                    FROM tasks 
                    WHERE user_id = ? AND year = ? AND month = ? AND day = ?
                ''', (current_user.id, year, month, day))
                tasks = cursor.fetchall()

                # Проверяем, есть ли просроченные задачи (для упрощения считаем просроченными задачи до текущей даты)
                has_overdue = False
                all_completed = False
                if tasks:
                    task_count = len(tasks)
                    cursor.execute('''
                        SELECT COUNT(*) 
                        FROM completed_tasks 
                        WHERE user_id = ? AND completion_time LIKE ?
                    ''', (current_user.id, f'{year}-{month:02d}-{day:02d}%'))
                    completed_count = cursor.fetchone()[0]
                    all_completed = task_count > 0 and completed_count == task_count

                    if year < today_year or (year == today_year and month < today_month) or (
                            year == today_year and month == today_month and day < today_day):
                        has_overdue = not all_completed

                # Формируем классы для ячейки
                classes = ['day-cell']
                if is_weekend:
                    classes.append('weekend')
                if is_today:
                    classes.append('today')
                if tasks:
                    classes.append('has-tasks')
                if has_overdue:
                    classes.append('has-overdue-tasks')
                if all_completed:
                    classes.append('all-tasks-completed')

                # Формируем HTML для дня
                calendar_html += f'<td class="{" ".join(classes)}">'
                calendar_html += f'<a href="#" class="day-link {"has-tasks" if tasks else ""}" data-day="{day}">'
                calendar_html += f'<span class="day-number">{day}</span>'
                if tasks:
                    # Подсчитываем задачи по приоритетам
                    priority_counts = {1: 0, 2: 0, 3: 0}
                    for task in tasks:
                        priority_counts[task['priority']] += 1

                    # Отображаем бейдж с наивысшим приоритетом
                    if priority_counts[3] > 0:
                        priority = 'high'
                        count = priority_counts[3]
                    elif priority_counts[2] > 0:
                        priority = 'medium'
                        count = priority_counts[2]
                    else:
                        priority = 'low'
                        count = priority_counts[1]
                    calendar_html += f'<span class="task-count-badge priority-{priority}">{count}</span>'
                calendar_html += '</a></td>'
            calendar_html += '</tr>'
        calendar_html += '</tbody></table>'

        return render_template('calendar.html',
                               year=year,
                               month=month,
                               russian_month_name=RUSSIAN_MONTHS[month],
                               calendar=calendar_html)

    @app.route('/calendar', defaults={'year': None, 'month': None})
    def show_calendar_default(year, month):
        now = datetime.now(pytz.UTC)
        return redirect(url_for('show_calendar', year=now.year, month=now.month))

    @app.route('/tasks/<int:year>/<int:month>/<int:day>', methods=['GET'])
    @login_required
    def get_tasks(year, month, day):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT id, task, time, priority, google_event_id 
            FROM tasks 
            WHERE user_id = ? AND year = ? AND month = ? AND day = ?
        ''', (current_user.id, year, month, day))
        tasks = cursor.fetchall()

        # Форматируем задачи для JSON-ответа
        tasks_list = []
        for task in tasks:
            tasks_list.append({
                'id': task['id'],
                'task': task['task'],
                'time': task['time'],
                'priority': task['priority'],
                'google_event_id': task['google_event_id']
            })

        # Категории пока не поддерживаются, но добавим пустой список для совместимости
        categories = []

        return jsonify({'tasks': tasks_list, 'categories': categories})

    @app.route('/add_task/<int:year>/<int:month>/<int:day>', methods=['POST'])
    @login_required
    def add_task(year, month, day):
        task_text = request.form.get('task')
        task_time = request.form.get('time')
        priority = request.form.get('priority', 1, type=int)

        if not task_text:
            flash('Задача не может быть пустой', 'error')
            return redirect(url_for('show_calendar', year=year, month=month))

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                INSERT INTO tasks (user_id, year, month, day, task, time, priority, created)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (current_user.id, year, month, day, task_text, task_time, priority, datetime.now()))
            db.commit()
            flash('Задача успешно добавлена', 'success')
        except Exception as e:
            flash(f'Ошибка при добавлении задачи: {str(e)}', 'error')

        return redirect(url_for('show_calendar', year=year, month=month))

    @app.route('/edit_task/<int:task_id>', methods=['POST'])
    @login_required
    def edit_task(task_id):
        task_text = request.form.get('task')
        task_time = request.form.get('time')
        priority = request.form.get('priority', 1, type=int)
        year = request.form.get('year', type=int)
        month = request.form.get('month', type=int)

        if not task_text:
            flash('Задача не может быть пустой', 'error')
            return redirect(url_for('show_calendar', year=year, month=month))

        try:
            db = get_db()
            cursor = db.cursor()
            # Проверяем, что задача принадлежит текущему пользователю
            cursor.execute('SELECT user_id FROM tasks WHERE id = ?', (task_id,))
            task = cursor.fetchone()
            if not task or task['user_id'] != current_user.id:
                flash('Задача не найдена или у вас нет прав для её редактирования', 'error')
                return redirect(url_for('show_calendar', year=year, month=month))

            cursor.execute('''
                UPDATE tasks 
                SET task = ?, time = ?, priority = ?
                WHERE id = ?
            ''', (task_text, task_time, priority, task_id))
            db.commit()
            flash('Задача успешно обновлена', 'success')
        except Exception as e:
            flash(f'Ошибка при обновлении задачи: {str(e)}', 'error')

        return redirect(url_for('show_calendar', year=year, month=month))

    @app.route('/delete_task/<int:task_id>', methods=['POST'])
    @login_required
    def delete_task(task_id):
        year = request.form.get('year', type=int)
        month = request.form.get('month', type=int)

        try:
            db = get_db()
            cursor = db.cursor()
            # Проверяем, что задача принадлежит текущему пользователю
            cursor.execute('SELECT user_id, google_event_id FROM tasks WHERE id = ?', (task_id,))
            task = cursor.fetchone()
            if not task or task['user_id'] != current_user.id:
                flash('Задача не найдена или у вас нет прав для её удаления', 'error')
                return redirect(url_for('show_calendar', year=year, month=month))

            # Если задача связана с Google Calendar, не удаляем её
            if task['google_event_id']:
                flash('Нельзя удалить задачу, синхронизированную с Google Calendar', 'error')
                return redirect(url_for('show_calendar', year=year, month=month))

            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            db.commit()
            flash('Задача успешно удалена', 'success')
        except Exception as e:
            flash(f'Ошибка при удалении задачи: {str(e)}', 'error')

        return redirect(url_for('show_calendar', year=year, month=month))

    @app.route('/complete_task/<int:task_id>', methods=['POST'])
    @login_required
    def complete_task(task_id):
        year = request.form.get('year', type=int)
        month = request.form.get('month', type=int)

        try:
            db = get_db()
            cursor = db.cursor()
            # Проверяем, что задача принадлежит текущему пользователю
            cursor.execute('SELECT user_id, task, priority, google_event_id FROM tasks WHERE id = ?', (task_id,))
            task = cursor.fetchone()
            if not task or task['user_id'] != current_user.id:
                flash('Задача не найдена или у вас нет прав для её завершения', 'error')
                return redirect(url_for('show_calendar', year=year, month=month))

            # Если задача связана с Google Calendar, не завершаем её
            if task['google_event_id']:
                flash('Нельзя завершить задачу, синхронизированную с Google Calendar', 'error')
                return redirect(url_for('show_calendar', year=year, month=month))

            # Добавляем задачу в completed_tasks
            cursor.execute('''
                INSERT INTO completed_tasks (user_id, task_text, priority, completion_time)
                VALUES (?, ?, ?, ?)
            ''', (current_user.id, task['task'], task['priority'], datetime.now().isoformat()))

            # Удаляем задачу из tasks
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            db.commit()
            flash('Задача успешно завершена', 'success')
        except Exception as e:
            flash(f'Ошибка при завершении задачи: {str(e)}', 'error')

        return redirect(url_for('show_calendar', year=year, month=month))

    @app.route('/completed_tasks/<int:year>/<int:month>/<int:day>', methods=['GET'])
    @login_required
    def get_completed_tasks(year, month, day):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT id, task_text, priority, completion_time 
            FROM completed_tasks 
            WHERE user_id = ? AND completion_time LIKE ?
        ''', (current_user.id, f'{year}-{month:02d}-{day:02d}%'))
        completed_tasks = cursor.fetchall()

        completed_tasks_list = []
        for task in completed_tasks:
            completed_tasks_list.append({
                'id': task['id'],
                'task_text': task['task_text'],
                'priority': task['priority'],
                'completion_time': task['completion_time']
            })

        return jsonify({'completed_tasks': completed_tasks_list})

    @app.route('/restore_task/<int:task_id>', methods=['POST'])
    @login_required
    def restore_task(task_id):
        year = request.form.get('year', type=int)
        month = request.form.get('month', type=int)
        day = request.form.get('day', type=int)

        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute('''
                SELECT user_id, task_text, priority, completion_time 
                FROM completed_tasks 
                WHERE id = ?
            ''', (task_id,))
            task = cursor.fetchone()
            if not task or task['user_id'] != current_user.id:
                flash('Задача не найдена или у вас нет прав для её восстановления', 'error')
                return redirect(url_for('show_calendar', year=year, month=month))

            # Восстанавливаем задачу в таблицу tasks
            completion_time = datetime.fromisoformat(task['completion_time'])
            cursor.execute('''
                INSERT INTO tasks (user_id, year, month, day, task, priority, created)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (current_user.id, year, month, day, task['task_text'], task['priority'], completion_time))

            # Удаляем задачу из completed_tasks
            cursor.execute('DELETE FROM completed_tasks WHERE id = ?', (task_id,))
            db.commit()
            flash('Задача успешно восстановлена', 'success')
        except Exception as e:
            flash(f'Ошибка при восстановлении задачи: {str(e)}', 'error')

        return redirect(url_for('show_calendar', year=year, month=month))