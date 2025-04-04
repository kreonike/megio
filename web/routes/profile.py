# profile.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
import sqlite3
from web.models.models import User


def profile_routes(app, get_db):
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        db = get_db()

        if request.method == 'POST' and 'email' in request.form:
            new_email = request.form.get('email')
            if not new_email:
                flash('Email не может быть пустым', 'error')
                return redirect(url_for('profile'))

            try:
                cursor = db.cursor()
                cursor.execute('UPDATE users SET email = ? WHERE id = ?', (new_email, current_user.id))
                db.commit()
                current_user.email = new_email
                flash('Email успешно обновлен', 'success')
            except sqlite3.IntegrityError:
                flash('Этот email уже используется другим пользователем', 'error')

        if not current_user.telegram_token:
            current_user.telegram_token = current_user.generate_telegram_token()

        return render_template('profile.html',
                               user=current_user,
                               telegram_linked=current_user.is_telegram_linked())