# telegram.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required, login_user
from web.models.models import User
from web.config.config import db_connection

def telegram_routes(app):
    @app.route('/link_telegram', methods=['GET', 'POST'])
    @login_required
    def link_telegram():
        if request.method == 'POST':
            telegram_id = request.form.get('telegram_id')

            if not telegram_id or not telegram_id.isdigit():
                flash('Неверный ID Telegram', 'error')
                return redirect(url_for('profile'))

            try:
                with db_connection() as db:
                    cursor = db.cursor()
                    cursor.execute('DELETE FROM telegram_users WHERE telegram_id = ? OR user_id = ?',
                                 (telegram_id, current_user.id))
                    cursor.execute('INSERT INTO telegram_users (telegram_id, user_id) VALUES (?, ?)',
                                 (telegram_id, current_user.id))
                    db.commit()
                    flash('Telegram аккаунт успешно привязан', 'success')
            except Exception as e:
                flash(f'Ошибка при привязке аккаунта: {str(e)}', 'error')

            return redirect(url_for('profile'))

        return render_template('link_telegram.html')

    @app.route('/telegram_auth/<token>')
    def telegram_auth(token):
        with db_connection() as db:
            cursor = db.cursor()
            cursor.execute('SELECT id, username, email FROM users WHERE telegram_token = ?', (token,))
            user_data = cursor.fetchone()

            if user_data:
                user = User(user_data['id'], user_data['username'], user_data['email'])
                login_user(user)
                flash('Вы успешно авторизованы через Telegram', 'success')
                return redirect(url_for('show_calendar'))

        flash('Неверная ссылка авторизации', 'error')
        return redirect(url_for('login'))