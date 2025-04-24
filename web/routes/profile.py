from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
import pytz
from web.config.config import db_connection
from web.services.category_service import get_user_categories, add_category, delete_category
from web.utils import log_action

def init_profile_routes(app):
    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        with db_connection() as db:
            categories = get_user_categories(db, current_user.id)

            if request.method == 'POST':
                app.logger.debug(f"[profile] POST request received, headers: {request.headers}, form: {request.form}")

                if 'email' in request.form or 'timezone' in request.form:
                    handle_profile_update(db, app.logger)

                if 'name' in request.form and 'color' in request.form:
                    name = request.form['name'].strip()
                    color = request.form['color'].strip()
                    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                    app.logger.debug(f"[profile] Adding category: name={name}, color={color}, is_ajax={is_ajax}")

                    if name and color:
                        try:
                            category_id = add_category(db, current_user.id, name, color, app.logger)
                            category_data = {'id': category_id, 'name': name, 'color': color}
                            if is_ajax:
                                app.logger.info(f"[profile] Category added successfully: {category_data}")
                                return jsonify({
                                    'success': True,
                                    'message': 'Категория успешно создана',
                                    'category': category_data
                                })
                            flash('Категория успешно создана', 'success')
                        except Exception as e:
                            app.logger.error(f"[profile] Category creation error: {str(e)}")
                            if is_ajax:
                                return jsonify({
                                    'success': False,
                                    'message': f'Ошибка создания категории: {str(e)}'
                                }), 400
                            flash('Ошибка создания категории', 'error')

                if 'delete_category' in request.form:
                    cat_id = request.form['delete_category']
                    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                    app.logger.debug(f"[profile] Deleting category: id={cat_id}, is_ajax={is_ajax}")

                    if delete_category(db, current_user.id, cat_id, app.logger):
                        if is_ajax:
                            app.logger.info(f"[profile] Category deleted successfully: id={cat_id}")
                            return jsonify({
                                'success': True,
                                'message': 'Категория успешно удалена',
                                'category_id': cat_id
                            })
                        flash('Категория успешно удалена', 'success')
                    else:
                        if is_ajax:
                            app.logger.warning(f"[profile] Category not found: id={cat_id}")
                            return jsonify({
                                'success': False,
                                'message': 'Категория не найдена'
                            }), 404
                        flash('Категория не найдена', 'error')

                # Для не-AJAX запросов рендерим шаблон
                if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    app.logger.debug("[profile] Rendering template for non-AJAX request")
                    return render_template(
                        'profile.html',
                        user=current_user,
                        categories=get_user_categories(db, current_user.id),
                        timezones=pytz.all_timezones,
                        telegram_linked=current_user.is_telegram_linked()
                    )

            # GET-запрос
            app.logger.debug("[profile] Handling GET request")
            return render_template(
                'profile.html',
                user=current_user,
                categories=categories,
                timezones=pytz.all_timezones,
                telegram_linked=current_user.is_telegram_linked()
            )

    def handle_profile_update(db, logger):
        try:
            cursor = db.cursor()
            updated = False

            if 'email' in request.form:
                new_email = request.form['email'].strip()
                if new_email:
                    cursor.execute('''
                        UPDATE users SET email = ? WHERE id = ?
                    ''', (new_email, current_user.id))
                    current_user.email = new_email
                    updated = True
                    flash('Email успешно обновлен', 'success')

            if 'timezone' in request.form:
                new_timezone = request.form['timezone']
                if new_timezone in pytz.all_timezones:
                    cursor.execute('''
                        UPDATE users SET timezone = ? WHERE id = ?
                    ''', (new_timezone, current_user.id))
                    current_user.timezone = new_timezone
                    updated = True
                    flash('Временная зона обновлена', 'success')

            if updated:
                db.commit()
                log_action(logger, "Profile", "updated", current_user.id)

        except Exception as e:
            db.rollback()
            logger.error(f"Profile update error: {str(e)}")
            flash('Ошибка обновления профиля', 'error')