# profile.py
import pytz
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
import sqlite3
from web.models.models import User


def profile_routes(app, get_db):
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        db = get_db()

        if request.method == 'POST':
            # Обработка email
            if 'email' in request.form:
                new_email = request.form.get('email')
                if not new_email:
                    flash('Email не может быть пустым', 'error')
                else:
                    try:
                        cursor = db.cursor()
                        cursor.execute('UPDATE users SET email = ? WHERE id = ?', (new_email, current_user.id))
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
                        cursor = db.cursor()
                        cursor.execute('UPDATE users SET timezone = ? WHERE id = ?', (new_timezone, current_user.id))
                        db.commit()
                        current_user.timezone = new_timezone
                        flash('Временная зона успешно обновлена', 'success')
                    except Exception as e:
                        flash(f'Ошибка при обновлении временной зоны: {str(e)}', 'error')

        if not current_user.telegram_token:
            current_user.telegram_token = current_user.generate_telegram_token()

        # Получаем все временные зоны из pytz
        timezones = pytz.all_timezones

        return render_template('profile.html',
                             user=current_user,
                             telegram_linked=current_user.is_telegram_linked(),
                             timezones=timezones)