# login.py
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user
from web.models.models import User

def login_routes(app, get_db, bcrypt):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT id, username, email, password FROM users WHERE username = ?', (username,))
            user_data = cursor.fetchone()

            if user_data and bcrypt.check_password_hash(user_data['password'], password):
                user = User(user_data['id'], user_data['username'], user_data['email'])
                login_user(user)
                return redirect(url_for('show_calendar'))
            else:
                flash('Неверное имя пользователя или пароль', 'error')
                return render_template('login.html')

        return render_template('login.html')