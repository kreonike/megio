from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from web.config.config import db_connection
from web.utils import json_response, log_category_action, log_error, handle_exceptions
from web.services.category_service import get_user_categories

def categories_routes(app):
    @app.route('/categories', methods=['GET', 'POST'])
    @login_required
    def manage_categories():
        with db_connection() as db:
            cursor = db.cursor()

            if request.method == 'POST':
                # Внутренняя функция для обработки POST-запроса
                @handle_exceptions
                def process_post():
                    if 'delete' in request.form:
                        cat_id = request.form.get('delete')
                        cursor.execute('''
                            DELETE FROM task_categories 
                            WHERE category_id = ? AND task_id IN (
                                SELECT id FROM tasks WHERE user_id = ?
                            )
                        ''', (cat_id, current_user.id))
                        cursor.execute('DELETE FROM categories WHERE id = ? AND user_id = ?',
                                       (cat_id, current_user.id))
                        if cursor.rowcount == 0:
                            raise ValueError('Категория не найдена или нет доступа')
                        db.commit()
                        log_category_action(app.logger, "deleted", cat_id, current_user.id)
                        return True, {'message': 'Категория удалена', 'category': 'success'}
                    else:
                        name = request.form.get('name')
                        color = request.form.get('color', '#3498db')
                        if not name:
                            raise ValueError('Название категории обязательно')
                        cursor.execute('INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)',
                                       (current_user.id, name, color))
                        db.commit()
                        log_category_action(app.logger, "added", None, current_user.id, name=name)
                        return True, {'message': 'Категория добавлена', 'category': 'success'}

                try:
                    success, flash_data = process_post()
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return json_response(True)
                    flash(flash_data['message'], flash_data['category'])
                    return redirect(url_for('manage_categories'))
                except ValueError as e:
                    # ValueError обрабатывается отдельно для flash-сообщений
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return json_response(False, error=str(e), status_code=400)
                    flash(str(e), 'error')
                    return redirect(url_for('manage_categories'))
                # Другие исключения обрабатываются декоратором handle_exceptions

            # GET запрос
            categories = get_user_categories(db, current_user.id)
            return render_template('categories.html', categories=categories)