MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

REMINDER_INTERVAL = 30  # seconds

# SQL-запросы для напоминаний
QUERY_24H = '''
    SELECT t.id, t.task, t.time, tu.telegram_id
    FROM tasks t
    JOIN telegram_users tu ON t.user_id = tu.user_id
    WHERE t.reminder_1day_sent = 0
    AND t.year = ? AND t.month = ? AND t.day = ?
    AND t.time IS NOT NULL
'''

QUERY_2H = '''
    SELECT t.id, t.task, t.time, tu.telegram_id
    FROM tasks t
    JOIN telegram_users tu ON t.user_id = tu.user_id
    WHERE t.reminder_2h_sent = 0
    AND t.year = ? AND t.month = ? AND t.day = ?
    AND t.time IS NOT NULL
'''

QUERY_15M = '''
    SELECT t.id, t.task, t.time, tu.telegram_id
    FROM tasks t
    JOIN telegram_users tu ON t.user_id = tu.user_id
    WHERE t.reminder_15m_sent = 0
    AND t.year = ? AND t.month = ? AND t.day = ?
    AND t.time IS NOT NULL
'''

UPDATE_REMINDER_STATUS = '''
    UPDATE tasks SET {} = 1 
    WHERE id = ?
'''
