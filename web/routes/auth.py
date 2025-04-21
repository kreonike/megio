# auth.py (объединенная версия)
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from web.config.config import db_connection
from web.models.models import User
from web.utils import log_action


def init_auth_routes(app, bcrypt):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('show_calendar'))

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
                        log_action(app.logger, "User", "logged in", user_data['id'])
                        flash('Вы успешно вошли в систему', 'success')
                        return redirect(url_for('show_calendar'))
                    else:
                        flash('Неверное имя пользователя или пароль', 'error')
            except Exception as e:
                app.logger.error(f"Login error: {str(e)}")
                flash('Произошла ошибка при входе в систему', 'error')

        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('show_calendar'))

        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            if not username or not email or not password:
                flash('Заполните все поля', 'error')
                return redirect(url_for('register'))

            try:
                with db_connection() as db:
                    cursor = db.cursor()
                    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
                    cursor.execute('''
                        INSERT INTO users (username, email, password, timezone) 
                        VALUES (?, ?, ?, ?)
                    ''', (username, email, password_hash, 'UTC'))
                    user_id = cursor.lastrowid
                    db.commit()

                    log_action(app.logger, "User", "registered", user_id)
                    flash('Регистрация прошла успешно. Теперь вы можете войти', 'success')
                    return redirect(url_for('login'))
            except Exception as e:
                app.logger.error(f"Registration error: {str(e)}")
                flash('Имя пользователя или email уже заняты', 'error')

        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        user_id = current_user.id
        logout_user()
        log_action(app.logger, "User", "logged out", user_id)
        flash('Вы успешно вышли из системы', 'success')
        return redirect(url_for('login'))