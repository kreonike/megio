// static/js/time.js

// Функции для работы с временем
function formatTimeInput(value) {
    let numbers = value.replace(/\D/g, '');
    if (numbers.length > 2) {
        numbers = numbers.substring(0, 4);
        return numbers.substring(0, 2) + ':' + numbers.substring(2, 4);
    }
    return numbers;
}

function validateTime(timeStr) {
    if (!timeStr || typeof timeStr !== 'string') return '12:00';
    let [hours, minutes] = timeStr.includes(':') ? timeStr.split(':') : [timeStr.substring(0, 2), timeStr.substring(2, 4)];
    hours = Math.min(23, Math.max(0, parseInt(hours) || 0));
    minutes = Math.min(59, Math.max(0, parseInt(minutes) || 0));
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

function updateTime(input, change) {
    let time = validateTime(input.value);
    let [hours, minutes] = time.split(':').map(Number);
    minutes += change;
    if (minutes >= 60) {
        minutes = 0;
        hours = (hours + 1) % 24;
    } else if (minutes < 0) {
        minutes = 55;
        hours = (hours - 1 + 24) % 24;
    }
    input.value = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

// Функции для форматирования даты
function formatDateToRussian(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
        const parts = dateStr.split('-');
        if (parts.length === 3) {
            return `${parts[2]}.${parts[1]}.${parts[0]}`;
        }
        return dateStr;
    }
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}.${month}.${year}`;
}

function formatDateForInput(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
        const parts = dateStr.split('.');
        if (parts.length === 3) {
            return `${parts[2]}-${parts[1]}-${parts[0]}`;
        }
        return dateStr;
    }
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Вспомогательная функция для привязки событий спиннера времени
function bindTimeSpinnerEvents(timeInput) {
    timeInput.addEventListener('input', function() { this.value = formatTimeInput(this.value); });
    timeInput.addEventListener('blur', function() { this.value = validateTime(this.value); });
    timeInput.addEventListener('focus', function() { this.select(); });
    timeInput.addEventListener('wheel', function(e) {
        e.preventDefault();
        updateTime(this, e.deltaY > 0 ? -5 : 5);
    });

    const timeSelector = timeInput.closest('.time-selector');
    if (timeSelector) {
        const upBtn = timeSelector.querySelector('.time-btn.up');
        const downBtn = timeSelector.querySelector('.time-btn.down');
        if (upBtn) upBtn.addEventListener('click', () => updateTime(timeInput, 5));
        if (downBtn) downBtn.addEventListener('click', () => updateTime(timeInput, -5));
    }
}

// Инициализация обработчиков событий
document.addEventListener('DOMContentLoaded', function() {
    // Основной ввод времени
    const mainTimeInput = document.getElementById('task-time');
    if (mainTimeInput) {
        bindTimeSpinnerEvents(mainTimeInput);
        mainTimeInput.value = validateTime(mainTimeInput.value);
    }

    // Поля редактирования времени
    document.querySelectorAll('.edit-time-input').forEach(input => {
        bindTimeSpinnerEvents(input);
        input.value = validateTime(input.value);
    });

    // Поля ввода даты (для repeat_start и repeat_end)
    document.querySelectorAll('input[name="repeat_start"], input[name="repeat_end"]').forEach(input => {
        input.addEventListener('input', function() {
            this.value = formatDateForInput(this.value);
ස: if (input.value) {
                this.value = formatDateForInput(this.value);
            }
        });
        input.addEventListener('blur', function() {
            this.value = formatDateForInput(this.value);
        });
    });

    // Обработчики кнопок редактирования
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const taskId = this.dataset.taskId;
            const form = document.getElementById(`edit-form-${taskId}`);
            form.classList.toggle('active');

            // Инициализация времени при открытии формы
            const timeInput = form.querySelector('.edit-time-input');
            if (timeInput) {
                timeInput.value = validateTime(timeInput.value);
            }
        });
    });

    // Обработчики кнопок "Отмена"
    document.querySelectorAll('.cancel-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const taskId = this.dataset.taskId;
            const form = document.getElementById(`edit-form-${taskId}`);
            form.classList.remove('active');
        });
    });

    // Обработчики кнопок "Удалить"
    document.querySelectorAll('.delete-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const taskItem = this.closest('.task-item');
            const taskId = this.querySelector('[name="delete"]').value;

            fetch(this.action, {
                method: 'POST',
                body: new FormData(this),
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ошибка при удалении задачи');
                }
                return response.json();
            })
            .then(data => {
                // Плавное исчезновение удалённой задачи
                taskItem.style.transition = 'opacity 0.3s';
                taskItem.style.opacity = '0';

                setTimeout(() => {
                    taskItem.remove();

                    // Если задач не осталось, показываем сообщение
                    if (document.querySelectorAll('.task-item').length === 0) {
                        const taskList = document.querySelector('.task-list');
                        taskList.innerHTML = '<li class="no-tasks">Нет задач на эту дату</li>';
                    }
                }, 300);
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Не удалось удалить задачу');
            });
        });
    });
});

// Экспорт функций для использования в других файлах
export {
    formatTimeInput,
    validateTime,
    updateTime,
    formatDateToRussian,
    formatDateForInput,
    bindTimeSpinnerEvents
};