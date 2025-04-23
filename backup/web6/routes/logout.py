# logout.py
from flask import redirect, url_for, flash
from flask_login import logout_user, login_required

def logout_routes(app):
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Вы успешно вышли из системы', 'success')
        return redirect(url_for('login'))