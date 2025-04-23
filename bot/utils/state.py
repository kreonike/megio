class UserState:
    def __init__(self):
        self.awaiting_task = False
        self.awaiting_task_text = False
        self.awaiting_task_time = False
        self.current_date = None
        self.current_task_text = None
        self.calendar_message_id = None  # ID сообщения с календарем
        self.last_tasks_message_id = None  # ID сообщения с задачами
        self.add_task_message_id = None  # Добавлено

# Словарь для хранения состояний пользователей, ключ — telegram_id
user_states = {}

def get_user_state(telegram_id):
    """Получить или создать состояние пользователя по telegram_id"""
    if telegram_id not in user_states:
        user_states[telegram_id] = UserState()
    return user_states[telegram_id]