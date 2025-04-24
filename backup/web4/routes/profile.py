# profile.py
import sqlite3

import pytz
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from web.config.config import db_connection

def profile_routes(app):
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if request.method == 'POST':
            # Обработка email
            if 'email' in request.form:
                new_email = request.form.get('email')
                if not new_email:
                    flash('Email не может быть пустым', 'error')
                else:
                    try:
                        with db_connection() as db:
                            cursor = db.cursor()
                            cursor.execute('UPDATE users SET email = ? WHERE id = ?',
                                         (new_email, current_user.id))
                            db.commit()
                            current_user.email = new_email
                            flash('Email успешно обновлен', 'success')
                    except sqlite3.IntegrityError:
                        flash('Этот email уже используется другим пользователем', 'error')

            # Обработка временной зоны
            if 'timezone' in request.form:
                new_timezone = request.form.get('timezone')
                if new_timezone in pytz.all_timezones:
                    try:
                        with db_connection() as db:
                            cursor = db.cursor()
                            cursor.execute('UPDATE users SET timezone = ? WHERE id = ?',
                                         (new_timezone, current_user.id))
                            db.commit()
                            current_user.timezone = new_timezone
                            flash('Временная зона успешно обновлена', 'success')
                    except Exception as e:
                        flash(f'Ошибка при обновлении временной зоны: {str(e)}', 'error')

        if not current_user.telegram_token:
            current_user.telegram_token = current_user.generate_telegram_token()

        timezones = pytz.all_timezones

        return render_template('profile.html',
                             user=current_user,
                             telegram_linked=current_user.is_telegram_linked(),
                             timezones=timezones)