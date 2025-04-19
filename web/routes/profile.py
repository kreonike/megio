# profile.py
import sqlite3
from datetime import datetime

import pytz
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required

from web.config.config import db_connection
from web.services.category_service import get_user_categories


def profile_routes(app):
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        categories = []
        with db_connection() as db:
            categories = get_user_categories(db, current_user.id)

        if request.method == 'POST':
            # Обработка основных данных профиля
            if 'email' in request.form or 'timezone' in request.form:
                handle_profile_update()

            # Обработка добавления категории
            if 'name' in request.form and 'color' in request.form:
                handle_add_category()

            # Обработка удаления категории
            if 'delete_category' in request.form:
                handle_delete_category()

        return render_template(
            'profile.html',
            user=current_user,
            categories=categories,
            timezones=pytz.all_timezones,
            telegram_linked=current_user.is_telegram_linked()
        )

    def handle_profile_update():
        """Обновление email и временной зоны"""
        try:
            with db_connection() as db:
                cursor = db.cursor()

                if 'email' in request.form:
                    new_email = request.form['email'].strip()
                    if not new_email:
                        flash('Email не может быть пустым', 'error')
                        return

                    cursor.execute('''
                        UPDATE users 
                        SET email = ?, updated_at = ?
                        WHERE id = ?
                    ''', (new_email, datetime.now(), current_user.id))
                    current_user.email = new_email
                    flash('Email успешно обновлен', 'success')

                if 'timezone' in request.form:
                    new_timezone = request.form['timezone']
                    if new_timezone in pytz.all_timezones:
                        cursor.execute('''
                            UPDATE users 
                            SET timezone = ?, updated_at = ?
                            WHERE id = ?
                        ''', (new_timezone, datetime.now(), current_user.id))
                        current_user.timezone = new_timezone
                        flash('Временная зона обновлена', 'success')

                db.commit()

        except sqlite3.IntegrityError as e:
            db.rollback()
            flash('Ошибка обновления: ' + str(e), 'error')

    def handle_add_category():
        """Добавление новой категории"""
        name = request.form['name'].strip()
        color = request.form['color'].strip()

        if not name or not color:
            flash('Заполните все поля', 'error')
            return

        try:
            with db_connection() as db:
                cursor = db.cursor()

                # Проверка существующей категории
                cursor.execute('''
                    SELECT id FROM categories 
                    WHERE user_id = ? AND LOWER(name) = LOWER(?)
                ''', (current_user.id, name))

                if cursor.fetchone():
                    flash('Категория с таким именем уже существует', 'error')
                    return

                # Добавление новой категории
                cursor.execute('''
                    INSERT INTO categories (user_id, name, color, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (current_user.id, name, color, datetime.now()))

                db.commit()
                flash('Категория успешно создана', 'success')

        except sqlite3.Error as e:
            db.rollback()
            flash('Ошибка создания категории: ' + str(e), 'error')

    def handle_delete_category():
        """Удаление категории"""
        cat_id = request.form['delete_category']

        try:
            with db_connection() as db:
                cursor = db.cursor()

                # Проверка владения категорией
                cursor.execute('''
                    SELECT user_id FROM categories 
                    WHERE id = ?
                ''', (cat_id,))

                result = cursor.fetchone()
                if not result or result['user_id'] != current_user.id:
                    flash('Категория не найдена', 'error')
                    return

                # Удаление связей с задачами
                cursor.execute('''
                    DELETE FROM task_categories 
                    WHERE category_id = ?
                ''', (cat_id,))

                # Удаление категории
                cursor.execute('''
                    DELETE FROM categories 
                    WHERE id = ?
                ''', (cat_id,))

                db.commit()
                flash('Категория успешно удалена', 'success')

        except sqlite3.Error as e:
            db.rollback()
            flash('Ошибка удаления: ' + str(e), 'error')

    return app