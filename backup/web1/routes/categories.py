# web/routes/categories.py
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user

from web.config.config import get_db

def categories_routes(app):
    @app.route('/categories', methods=['GET', 'POST'])
    @login_required
    def manage_categories():
        db = get_db()
        cursor = db.cursor()

        if request.method == 'POST':
            if 'delete' in request.form:
                cat_id = request.form.get('delete')
                cursor.execute('DELETE FROM categories WHERE id = ? AND user_id = ?',
                               (cat_id, current_user.id))
                db.commit()
                flash('Категория удалена', 'success')
            else:
                name = request.form.get('name')
                color = request.form.get('color', '#3498db')
                if name:
                    cursor.execute('INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)',
                                   (current_user.id, name, color))
                    db.commit()
                    flash('Категория добавлена', 'success')

            return redirect(url_for('manage_categories'))

        # GET запрос
        cursor.execute('SELECT id, name, color FROM categories WHERE user_id = ?',
                       (current_user.id,))
        categories = cursor.fetchall()

        return render_template('categories.html', categories=categories)