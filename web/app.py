import calendar
import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, flash, json, jsonify
from flask import url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, current_user

from web.logging_config import configure_logging
from web.routes.stats import stats_routes

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
import datetime as dt
from web.config.config import init_db

from web.models.models import User
from web.routes.profile import profile_routes
from web.routes.telegram import telegram_routes
from web.routes.register import register_routes
from web.routes.login import login_routes
from web.routes.logout import logout_routes
from web.routes.google import google_routes, google_sync_scheduler
#from web.routes.categories import categories_routes
from web.routes.task_restore import task_restore_routes
from web.routes.categories import categories_routes
from web.routes.remind import remind_routes
from web.routes.calendar import generate_calendar
from web.routes.complete import complete_routes
from web.routes.tasks import tasks_routes


import atexit

# Импорт конфигурации
from web.config.config import (
    SECRET_KEY, MONTH_NAMES, get_db, close_db
)

app = Flask(__name__)

from web.config.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, SCOPES

app.config['GOOGLE_CLIENT_ID'] = GOOGLE_CLIENT_ID
app.config['GOOGLE_CLIENT_SECRET'] = GOOGLE_CLIENT_SECRET
app.config['GOOGLE_REDIRECT_URI'] = GOOGLE_REDIRECT_URI
app.config['SCOPES'] = SCOPES

bcrypt = Bcrypt(app)
app.secret_key = SECRET_KEY



# Настройка логирования
configure_logging(app)
logger = app.logger

# Инициализация маршрутов
profile_routes(app, get_db)
telegram_routes(app, get_db)
register_routes(app, get_db, bcrypt)
login_routes(app, get_db, bcrypt)
logout_routes(app)
google_routes(app, get_db)
stats_routes(app, get_db)
task_restore_routes(app, get_db)
categories_routes(app)
remind_routes(app)
complete_routes(app, get_db)
tasks_routes(app, get_db)
#categories_routes(app, get_db)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Инициализация Google Scheduler
logger.info("Initializing Google Scheduler...")
if not hasattr(app, 'google_scheduler') and (not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'):
    app.google_scheduler = google_sync_scheduler(app, get_db)
    app.google_scheduler.start()
    atexit.register(lambda: app.google_scheduler.shutdown())

app.teardown_appcontext(close_db)
init_db(app)


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id, username, email, telegram_token, google_token FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['email'],
                    user_data['telegram_token'], user_data['google_token'])


# def generate_calendar(year, month, user_id):
#     cal = calendar.Calendar()
#     month_days = cal.monthdayscalendar(year, month)
#     now = datetime.now()
#     current_day = now.day if (year == now.year and month == now.month) else None
#
#     db = get_db()
#     cursor = db.cursor()
#
#     # Получаем количество задач и максимальный приоритет по дням
#     cursor.execute('''
#         SELECT day, COUNT(*) as task_count, MAX(priority) as max_priority
#         FROM tasks
#         WHERE user_id = ? AND year = ? AND month = ?
#         GROUP BY day
#     ''', (user_id, year, month))
#     days_tasks = {row['day']: {'count': row['task_count'], 'priority': row['max_priority']}
#                   for row in cursor.fetchall()}
#
#     # Получаем задачи с категориями
#     cursor.execute('''
#         SELECT t.day, c.color
#         FROM tasks t
#         JOIN task_categories tc ON t.id = tc.task_id
#         JOIN categories c ON tc.category_id = c.id
#         WHERE t.user_id = ? AND t.year = ? AND t.month = ?
#     ''', (user_id, year, month))
#
#     days_colors = {}
#     for row in cursor.fetchall():
#         day = row['day']
#         if day not in days_colors:
#             days_colors[day] = set()
#         days_colors[day].add(row['color'])
#
#     # Начинаем формировать HTML календаря
#     calendar_html = '<table class="calendar-table"><tr>'
#     calendar_html += ''.join(f'<th>{day}</th>' for day in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'])
#     calendar_html += '</tr>'
#
#     for week in month_days:
#         calendar_html += '<tr>'
#         for i, day in enumerate(week):
#             if day == 0:
#                 calendar_html += '<td class="empty-day"></td>'
#                 continue
#
#             classes = ['day-cell']
#             if day == current_day:
#                 classes.append('today')
#             if day in days_tasks:
#                 classes.append('has-tasks')
#             if i >= 5:
#                 classes.append('weekend')
#
#             # Добавляем стили для категорий
#             style = ''
#             if day in days_colors:
#                 colors = days_colors[day]
#                 if len(colors) == 1:
#                     style = f"background-color: {next(iter(colors))}20;"  # 20 - прозрачность
#                 else:
#                     gradient = ','.join([f"{color} 0%, {color} 50%" for color in colors])
#                     style = f"background: linear-gradient(135deg, {gradient});"
#
#             task_info = days_tasks.get(day, {})
#             task_count = task_info.get('count', 0)
#             priority = task_info.get('priority', 1)
#
#             priority_class = ''
#             if priority == 3:
#                 priority_class = 'priority-high'
#             elif priority == 2:
#                 priority_class = 'priority-medium'
#             else:
#                 priority_class = 'priority-low'
#
#             task_count_html = f'<span class="task-count-badge {priority_class}">{task_count}</span>' if task_count > 0 else ''
#
#             calendar_html += f'''
#                 <td class="{" ".join(classes)}" style="{style}">
#                     <a href="{url_for("day_tasks", year=year, month=month, day=day)}" class="day-link" data-day="{day}">
#                         <span class="day-number">{day}</span>
#                         {task_count_html}
#                     </a>
#                 </td>
#             '''
#         calendar_html += '</tr>'
#
#     calendar_html += '</table>'
#     return calendar_html


# @app.route('/')
# @login_required
# def show_calendar():
#     now = datetime.now()
#     year = request.args.get('year', default=now.year, type=int)
#     month = request.args.get('month', default=now.month, type=int)
#
#     if month > 12:
#         month = 1
#         year += 1
#     elif month < 1:
#         month = 12
#         year -= 1
#
#     # Получаем категории пользователя
#     db = get_db()
#     cursor = db.cursor()
#     cursor.execute('SELECT id, name, color FROM categories WHERE user_id = ?', (current_user.id,))
#     categories = cursor.fetchall()
#
#     calendar_html = generate_calendar(year, month, current_user.id, get_db)
#     return render_template('calendar.html',
#                            calendar=calendar_html,
#                            year=year,
#                            month=month,
#                            russian_month_name=MONTH_NAMES[month],
#                            username=current_user.username,
#                            categories=categories)


# @app.route('/tasks/<int:year>/<int:month>/<int:day>', methods=['GET', 'POST'])
# @login_required
# def day_tasks(year, month, day):
#     logger.info(f"Received task form data: {request.form}")
#     db = get_db()
#     cursor = db.cursor()
#
#     try:
#         cursor.execute('SELECT id, name, color FROM categories WHERE user_id = ?', (current_user.id,))
#         categories = cursor.fetchall()
#
#         if request.method == 'POST':
#             # Удаление задачи
#             if 'delete' in request.form:
#                 task_id = request.form.get('delete')
#                 cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, current_user.id))
#                 cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
#                 db.commit()
#                 if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                     return jsonify({'status': 'success'})
#                 flash('Задача удалена', 'success')
#
#             # Редактирование задачи
#             elif 'task_id' in request.form:
#                 task_id = request.form.get('task_id')
#                 new_task = request.form.get('task')
#                 new_time = request.form.get('time')
#                 priority = request.form.get('priority', 1)
#                 category_ids = request.form.getlist('categories')
#                 repeat_enabled = 'repeat_enabled' in request.form
#                 repeat_days = request.form.get('repeat_days') if repeat_enabled else None
#                 repeat_start = request.form.get('repeat_start') if repeat_enabled else None
#                 repeat_end = request.form.get('repeat_end') if repeat_enabled else None
#
#                 if new_task:
#                     cursor.execute('''
#                         UPDATE tasks
#                         SET task = ?, time = ?,
#                             repeat_days = ?,
#                             repeat_start = ?,
#                             repeat_end = ?,
#                             priority = ?
#                         WHERE id = ? AND user_id = ?
#                     ''', (
#                         new_task,
#                         new_time,
#                         int(repeat_days) if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
#                         repeat_start if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
#                         repeat_end if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
#                         priority,
#                         task_id,
#                         current_user.id
#                     ))
#
#                     cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
#                     for cat_id in category_ids:
#                         cursor.execute('INSERT INTO task_categories (task_id, category_id) VALUES (?, ?)',
#                                        (task_id, cat_id))
#
#                     db.commit()
#                     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                         return jsonify({'status': 'success'})
#                     flash('Задача обновлена', 'success')
#
#             # Добавление новой задачи
#             elif 'task' in request.form and 'date' in request.form:
#                 task_text = request.form.get('task')
#                 task_time = request.form.get('time')
#                 priority = request.form.get('priority', 1)
#                 category_ids = request.form.getlist('categories')
#                 repeat_enabled = 'repeat_enabled' in request.form
#                 repeat_days = request.form.get('repeat_days') if repeat_enabled else None
#                 repeat_start = request.form.get('repeat_start') if repeat_enabled else None
#                 repeat_end = request.form.get('repeat_end') if repeat_enabled else None
#                 date = request.form.get('date')
#                 date_parts = date.split('-')
#                 year, month, day = map(int, date_parts)
#
#                 if task_text:
#                     cursor.execute('''
#                         INSERT INTO tasks (user_id, year, month, day, task, time, repeat_days, repeat_start, repeat_end, priority)
#                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                     ''', (
#                         current_user.id,
#                         year,
#                         month,
#                         day,
#                         task_text,
#                         task_time,
#                         int(repeat_days) if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
#                         repeat_start if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
#                         repeat_end if repeat_enabled and repeat_days and int(repeat_days) > 0 else None,
#                         priority
#                     ))
#
#                     task_id = cursor.lastrowid
#                     for cat_id in category_ids:
#                         cursor.execute('INSERT INTO task_categories (task_id, category_id) VALUES (?, ?)',
#                                        (task_id, cat_id))
#
#                     db.commit()
#                     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                         return jsonify({'status': 'success', 'task_id': task_id})
#                     flash('Задача добавлена', 'success')
#
#             if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
#                 return redirect(url_for('day_tasks', year=year, month=month, day=day))
#
#         # GET-запрос
#         cursor.execute('''
#             SELECT t.id, t.task, t.time, t.created, t.repeat_days, t.repeat_start, t.repeat_end, t.priority,
#                    GROUP_CONCAT(tc.category_id) AS category_ids
#             FROM tasks t
#             LEFT JOIN task_categories tc ON t.id = tc.task_id
#             WHERE t.user_id = ? AND t.year = ? AND t.month = ? AND t.day = ?
#             GROUP BY t.id
#             ORDER BY t.priority DESC, t.time, t.created
#         ''', (current_user.id, year, month, day))
#         tasks = []
#         for row in cursor.fetchall():
#             task = dict(row)
#             try:
#                 task['category_ids'] = list(map(int, task['category_ids'].split(','))) if task['category_ids'] else []
#             except (ValueError, TypeError) as e:
#                 logger.error(f"Error processing category_ids for task {task['id']}: {e}")
#                 task['category_ids'] = []
#             tasks.append(task)
#         logger.info(f"Tasks data for day {year}-{month}-{day}: {tasks}")
#
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return jsonify({'tasks': tasks, 'date': f"{year}-{month:02d}-{day:02d}", 'categories': [dict(cat) for cat in categories]})
#
#         date_str = f"{day:02d}.{month:02d}.{year}"
#         return render_template('tasks.html', year=year, month=month, day=day, date_str=date_str,
#                                tasks=tasks, categories=categories)
#
#     except Exception as e:
#         logger.error(f"Error in day_tasks: {str(e)}", exc_info=True)
#         return jsonify({'error': str(e)}), 500


# @app.route('/tasks/<int:year>/<int:month>', methods=['GET'])
# @login_required
# def month_tasks(year, month):
#     db = get_db()
#     cursor = db.cursor()
#
#     # Получаем задачи по дням месяца
#     cursor.execute('''
#         SELECT day, task, priority
#         FROM tasks
#         WHERE user_id = ? AND year = ? AND month = ?
#         ORDER BY day
#     ''', (current_user.id, year, month))
#
#     tasks_by_day = {}
#     for row in cursor.fetchall():
#         day = row['day']
#         if day not in tasks_by_day:
#             tasks_by_day[day] = []
#         tasks_by_day[day].append({
#             'task': row['task'],
#             'priority': row['priority']
#         })
#
#     # Добавляем все дни месяца, даже если задач нет
#     import calendar
#     cal = calendar.Calendar()
#     month_days = cal.itermonthdays(year, month)
#     for day in month_days:
#         if day != 0 and day not in tasks_by_day:
#             tasks_by_day[day] = []
#
#     return jsonify({'tasksByDay': tasks_by_day})


# @app.route('/tasks/<int:year>/<int:month>/<int:day>/complete', methods=['POST'])
# @login_required
# def complete_task(year, month, day):
#     if not request.is_json:
#         return jsonify({'success': False, 'error': 'Invalid content type'}), 400
#
#     data = request.get_json()
#     task_id = data.get('task_id')
#
#     if not task_id:
#         return jsonify({'success': False, 'error': 'Missing task_id'}), 400
#
#     db = get_db()
#     cursor = db.cursor()
#
#     try:
#         # 1. Получаем данные задачи
#         cursor.execute('''
#             SELECT id, user_id, task, priority
#             FROM tasks
#             WHERE id = ? AND user_id = ?
#         ''', (task_id, current_user.id))
#         task = cursor.fetchone()
#
#         if not task:
#             return jsonify({'success': False, 'error': 'Task not found'}), 404
#
#         # 2. Получаем категории задачи
#         cursor.execute('''
#             SELECT c.name
#             FROM categories c
#             JOIN task_categories tc ON c.id = tc.category_id
#             WHERE tc.task_id = ?
#         ''', (task_id,))
#         categories = [row['name'] for row in cursor.fetchall()]
#
#         # 3. Переносим в таблицу выполненных задач с правильными именами столбцов
#         cursor.execute('''
#             INSERT INTO completed_tasks
#             (user_id, task_id, task_text, priority, categories, original_year, original_month, original_day)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (
#             current_user.id,
#             task_id,
#             task['task'],
#             task['priority'],
#             ','.join(categories) if categories else None,
#             year,
#             month,
#             day
#         ))
#
#         # 4. Удаляем из текущих задач
#         cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
#
#         # 5. Удаляем связи с категориями
#         cursor.execute('DELETE FROM task_categories WHERE task_id = ?', (task_id,))
#
#         db.commit()
#
#         return jsonify({'success': True})
#
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Ошибка при выполнении задачи: {str(e)}")
#         return jsonify({'success': False, 'error': str(e)}), 500


# @app.route('/tasks/<int:year>/<int:month>/<int:day>/completed', methods=['GET'])
# @login_required
# def get_completed_tasks(year, month, day):
#     db = get_db()
#     cursor = db.cursor()
#
#     try:
#         cursor.execute('''
#             SELECT id, task_id, task_text, priority, categories,
#                    datetime(completion_time, 'localtime') as completion_time
#             FROM completed_tasks
#             WHERE user_id = ? AND original_year = ? AND original_month = ? AND original_day = ?
#             ORDER BY completion_time DESC
#         ''', (current_user.id, year, month, day))
#
#         completed_tasks = [dict(row) for row in cursor.fetchall()]
#
#         return jsonify({
#             'completed_tasks': completed_tasks,
#             'date': f"{year}-{month:02d}-{day:02d}"
#         })
#     except Exception as e:
#         logger.error(f"Error fetching completed tasks: {str(e)}")
#         return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
