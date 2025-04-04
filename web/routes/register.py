# register.py
from flask import render_template, redirect, url_for, flash, request
import sqlite3
import re

def register_routes(app, get_db, bcrypt):
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            if not username or not email or not password:
                flash('Заполните все поля', 'error')
                return render_template('register.html')

            # Email validation
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash('Введите корректный email', 'error')
                return render_template('register.html')

            # Password complexity check
            if (len(password) < 8 or
                    not re.search(r'[A-Z]', password) or
                    not re.search(r'[a-z]', password) or
                    not re.search(r'\d', password)):
                flash('Пароль должен содержать минимум 8 символов, включая цифры, заглавные и строчные буквы', 'error')
                return render_template('register.html')

            # Используем flask_bcrypt для хеширования
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            try:
                db = get_db()
                cursor = db.cursor()
                cursor.execute('''
                    INSERT INTO users (username, email, password)
                    VALUES (?, ?, ?)
                ''', (username, email, hashed_password))
                db.commit()

                flash('Регистрация успешна. Теперь вы можете войти.', 'success')
                return redirect(url_for('login'))

            except sqlite3.IntegrityError as e:
                if 'username' in str(e):
                    flash('Это имя пользователя уже занято', 'error')
                elif 'email' in str(e):
                    flash('Этот email уже используется', 'error')
                return render_template('register.html')

        return render_template('register.html')