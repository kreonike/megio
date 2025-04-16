from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from web.config.config import db_connection
from web.utils import json_response, log_action, log_error, handle_exceptions, handle_crud_post
from web.services.category_service import get_user_categories, get_default_categories


def categories_routes(app):
    def handle_delete(db):
        cat_id = request.form.get('delete')
        if not cat_id:
            raise ValueError('Идентификатор категории обязателен')
        cursor = db.cursor()
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
        log_action(app.logger, "Category", "deleted", current_user.id, entity_id=cat_id)
        return True, {'message': 'Категория удалена', 'category': 'success'}

    def handle_add(db):
        name = request.form.get('name')
        color = request.form.get('color', '#3498db')
        if not name:
            raise ValueError('Название категории обязательно')
        cursor = db.cursor()
        cursor.execute('INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)',
                       (current_user.id, name, color))
        db.commit()
        log_action(app.logger, "Category", "added", current_user.id, name=name)
        return True, {'message': 'Категория добавлена', 'category': 'success'}

    @app.route('/categories', methods=['GET', 'POST'])
    @login_required
    @handle_crud_post(
        action_handlers=lambda db: {
            'delete': lambda: handle_delete(db),
            'add': lambda: handle_add(db)
        },
        redirect_endpoint='manage_categories'
    )
    def manage_categories():
        with db_connection() as db:
            categories = get_user_categories(db, current_user.id)
            if not categories:
                categories = get_default_categories(db, current_user.id)
            return render_template('categories.html', categories=categories)