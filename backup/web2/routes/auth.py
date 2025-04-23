# web/routes/auth.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from web.models.models import User

def auth_routes(app, get_db):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('show_calendar'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                flash('Введите имя пользователя и пароль', 'error')
                return redirect(url_for('login'))

            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT id, username, password_hash, email, telegram_token, google_token, timezone FROM users WHERE username = ?', (username,))
            user_data = cursor.fetchone()

            if user_data and check_password_hash(user_data['password_hash'], password):
                user = User(user_data['id'], user_data['username'], user_data['password_hash'], user_data['email'], user_data['telegram_token'], user_data['google_token'], user_data['timezone'])
                login_user(user)
                flash('Вы успешно вошли в систему', 'success')
                return redirect(url_for('show_calendar'))
            else:
                flash('Неверное имя пользователя или пароль', 'error')

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

            db = get_db()
            cursor = db.cursor()

            try:
                password_hash = generate_password_hash(password)
                cursor.execute('INSERT INTO users (username, email, password_hash, timezone) VALUES (?, ?, ?, ?)',
                               (username, email, password_hash, 'UTC'))
                db.commit()
                flash('Регистрация прошла успешно. Теперь вы можете войти', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Имя пользователя или email уже заняты', 'error')

        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Вы вышли из системы', 'success')
        return redirect(url_for('login'))