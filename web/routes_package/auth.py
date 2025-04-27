# auth.py
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import random
import string
import re
import sqlite3
from web.config.config import db_connection
from web.models.models import User
from web.utils import log_action

def init_auth_routes(app, bcrypt):
    def generate_strong_password(length=12):
        """Генерирует надежный пароль с гарантированными типами символов"""
        lower = string.ascii_lowercase
        upper = string.ascii_uppercase
        digits = string.digits
        symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?'

        # Гарантируем минимум по одному символу каждого типа
        password = [
            random.choice(lower),
            random.choice(upper),
            random.choice(digits),
            random.choice(symbols)
        ]

        # Заполняем оставшуюся длину случайными символами
        all_chars = lower + upper + digits + symbols
        password.extend(random.choice(all_chars) for _ in range(length - 4))

        # Перемешиваем и объединяем
        random.shuffle(password)
        return ''.join(password)

    @app.route('/generate-password', methods=['GET'])
    def generate_password():
        """API endpoint для генерации пароля"""
        password = generate_strong_password()
        return jsonify({'password': password})

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
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')

            # Валидация
            errors = False

            if not username or len(username) < 3:
                flash('Имя пользователя должно содержать минимум 3 символа', 'error')
                errors = True

            if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash('Введите корректный email', 'error')
                errors = True

            if (not password or len(password) < 8 or
                    not re.search(r'[A-Z]', password) or
                    not re.search(r'[a-z]', password) or
                    not re.search(r'\d', password)):
                flash('Пароль должен содержать минимум 8 символов, включая цифры, заглавные и строчные буквы', 'error')
                errors = True

            if errors:
                return render_template('register.html',
                                    username=username,
                                    email=email)

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
            except sqlite3.IntegrityError as e:
                if 'username' in str(e):
                    flash('Это имя пользователя уже занято', 'error')
                elif 'email' in str(e):
                    flash('Этот email уже используется', 'error')
                return render_template('register.html',
                                    username=username,
                                    email=email)
            except Exception as e:
                flash(f'Ошибка при регистрации: {str(e)}', 'error')
                return render_template('register.html',
                                    username=username,
                                    email=email)

        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        user_id = current_user.id
        logout_user()
        log_action(app.logger, "User", "logged out", user_id)
        flash('Вы успешно вышли из системы', 'success')
        return redirect(url_for('login'))