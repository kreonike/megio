from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from web.config.config import db_connection
from web.utils import json_response, log_category_action, log_error
from web.services.category_service import get_user_categories

def categories_routes(app):
    @app.route('/categories', methods=['GET', 'POST'])
    @login_required
    def manage_categories():
        with db_connection() as db:
            cursor = db.cursor()

            if request.method == 'POST':
                try:
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
                            flash('Категория не найдена или нет доступа', 'error')
                        else:
                            flash('Категория удалена', 'success')
                            db.commit()
                            log_category_action(app.logger, "deleted", cat_id, current_user.id)
                    else:
                        name = request.form.get('name')
                        color = request.form.get('color', '#3498db')
                        if not name:
                            flash('Название категории обязательно', 'error')
                        else:
                            cursor.execute('INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)',
                                           (current_user.id, name, color))
                            db.commit()
                            flash('Категория добавлена', 'success')
                            log_category_action(app.logger, "added", None, current_user.id, name=name)

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return json_response(True)
                    return redirect(url_for('manage_categories'))

                except Exception as e:
                    log_error(app.logger, f"Error managing category: {str(e)}", exc_info=True)
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return json_response(False, error=str(e), status_code=500)
                    flash(f'Ошибка: {str(e)}', 'error')
                    return redirect(url_for('manage_categories'))

            # GET запрос
            categories = get_user_categories(db, current_user.id)
            return render_template('categories.html', categories=categories)