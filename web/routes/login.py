# login.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user
from web.models.models import User
from web.config.config import db_connection

def login_routes(app, bcrypt):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            try:
                with db_connection() as db:
                    cursor = db.cursor()
                    cursor.execute('''
                        SELECT id, username, email, password, telegram_token, google_token, timezone 
                        FROM users 
                        WHERE username = ?
                    ''', (username,))
                    user_data = cursor.fetchone()

                    if user_data and bcrypt.check_password_hash(user_data['password'], password):
                        user = User(
                            user_id=user_data['id'],
                            username=user_data['username'],
                            email=user_data['email'],
                            telegram_token=user_data['telegram_token'],
                            google_token=user_data['google_token'],
                            timezone=user_data['timezone']
                        )
                        login_user(user)
                        flash('Вы успешно вошли в систему', 'success')
                        return redirect(url_for('show_calendar'))
                    else:
                        flash('Неверное имя пользователя или пароль', 'error')
            except Exception as e:
                app.logger.error(f"Ошибка при входе: {str(e)}")
                flash('Произошла ошибка при входе в систему', 'error')

        return render_template('login.html')