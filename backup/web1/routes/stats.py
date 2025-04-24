# web/routes/stats.py
from flask import render_template, request, jsonify
from flask_login import login_required, current_user

def stats_routes(app, get_db):
    @app.route('/stats', endpoint='stats')
    @login_required
    def show_stats():
        db = get_db()
        cursor = db.cursor()

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        priority = request.args.get('priority')

        query = '''
            SELECT 
                strftime('%Y-%m', completion_time) as month,
                COUNT(*) as total,
                SUM(CASE WHEN priority = 3 THEN 1 ELSE 0 END) as high_priority,
                SUM(CASE WHEN priority = 2 THEN 1 ELSE 0 END) as medium_priority,
                SUM(CASE WHEN priority = 1 THEN 1 ELSE 0 END) as low_priority
            FROM completed_tasks
            WHERE user_id = ?
        '''
        params = [current_user.id]

        if start_date:
            query += " AND completion_time >= ?"
            params.append(start_date)
        if end_date:
            query += " AND completion_time <= ?"
            params.append(end_date + " 23:59:59")
        if priority:
            query += " AND priority = ?"
            params.append(int(priority))

        query += " GROUP BY strftime('%Y-%m', completion_time) ORDER BY month DESC"

        cursor.execute(query, params)
        stats = [dict(row) for row in cursor.fetchall()]

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'stats': stats})
        return render_template('stats.html', stats=stats)

    @app.route('/stats/tasks', methods=['GET'])
    @login_required
    def get_tasks():
        db = get_db()
        cursor = db.cursor()

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        priority = request.args.get('priority')

        query = '''
            SELECT task_text, priority, completion_time
            FROM completed_tasks
            WHERE user_id = ?
        '''
        params = [current_user.id]

        if start_date:
            query += " AND completion_time >= ?"
            params.append(start_date)
        if end_date:
            query += " AND completion_time <= ?"
            params.append(end_date + " 23:59:59")
        if priority:
            query += " AND priority = ?"
            params.append(int(priority))

        query += " ORDER BY completion_time DESC"

        cursor.execute(query, params)
        tasks = [dict(row) for row in cursor.fetchall()]

        return jsonify({'tasks': tasks})