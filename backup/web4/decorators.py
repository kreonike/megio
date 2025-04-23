# from functools import wraps
# from flask import jsonify, request
# from flask_login import current_user
# from web.utils import json_response
# from web.config.config import db_connection
#
# def check_task_owner(f):
#     @wraps(f)
#     def wrapped(*args, **kwargs):
#         task_id = kwargs.get('task_id') or request.form.get('task_id') or (request.get_json() or {}).get('task_id')
#         if task_id:
#             with db_connection() as db:
#                 cursor = db.cursor()
#                 cursor.execute('SELECT user_id FROM tasks WHERE id = ?', (task_id,))
#                 task = cursor.fetchone()
#                 if not task or task['user_id'] != current_user.id:
#                     return json_response(False, error='No access to task', status_code=403)
#         return f(*args, **kwargs)
#     return wrapped