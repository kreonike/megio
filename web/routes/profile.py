# profile.py (оптимизированная версия)
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
import pytz
from web.config.config import db_connection
from web.services.category_service import get_user_categories, add_category, delete_category
from web.utils import log_action


def init_profile_routes(app):
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        with db_connection() as db:
            categories = get_user_categories(db, current_user.id)

            if request.method == 'POST':
                if 'email' in request.form or 'timezone' in request.form:
                    handle_profile_update(db, app.logger)

                if 'name' in request.form and 'color' in request.form:
                    name = request.form['name'].strip()
                    color = request.form['color'].strip()
                    if name and color:
                        try:
                            add_category(db, current_user.id, name, color, app.logger)
                            flash('Категория успешно создана', 'success')
                        except Exception as e:
                            app.logger.error(f"Category creation error: {str(e)}")
                            flash('Ошибка создания категории', 'error')

                if 'delete_category' in request.form:
                    cat_id = request.form['delete_category']
                    if delete_category(db, current_user.id, cat_id, app.logger):
                        flash('Категория успешно удалена', 'success')
                    else:
                        flash('Категория не найдена', 'error')

        return render_template(
            'profile.html',
            user=current_user,
            categories=categories,
            timezones=pytz.all_timezones,
            telegram_linked=current_user.is_telegram_linked()
        )

    def handle_profile_update(db, logger):
        try:
            cursor = db.cursor()
            updated = False

            if 'email' in request.form:
                new_email = request.form['email'].strip()
                if new_email:
                    cursor.execute('''
                        UPDATE users SET email = ? WHERE id = ?
                    ''', (new_email, current_user.id))
                    current_user.email = new_email
                    updated = True
                    flash('Email успешно обновлен', 'success')

            if 'timezone' in request.form:
                new_timezone = request.form['timezone']
                if new_timezone in pytz.all_timezones:
                    cursor.execute('''
                        UPDATE users SET timezone = ? WHERE id = ?
                    ''', (new_timezone, current_user.id))
                    current_user.timezone = new_timezone
                    updated = True
                    flash('Временная зона обновлена', 'success')

            if updated:
                db.commit()
                log_action(logger, "Profile", "updated", current_user.id)

        except Exception as e:
            db.rollback()
            logger.error(f"Profile update error: {str(e)}")
            flash('Ошибка обновления профиля', 'error')