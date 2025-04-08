// static/js/tasks.js
import { updateTasksSection, updateCalendar } from './calendar-update.js';
import { fetchCompletedTasks } from './completed-tasks.js';

export function bindAllTaskHandlers(year, month) {
    console.log('[bindAllTaskHandlers] Binding all task handlers');
    bindTaskFormHandler(year, month);
    bindEditHandlers(year, month);
    bindDeleteHandlers(year, month);
    bindCompleteHandlers(year, month);
}

function bindTaskFormHandler(year, month) {
    const taskForm = document.querySelector('.task-form');
    if (taskForm) {
        taskForm.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('[bindTaskFormHandler] Task form submitted');

            const formData = new FormData(this);
            const repeatEnabled = formData.get('repeat_enabled') === 'on';
            if (!repeatEnabled) {
                formData.delete('repeat_days');
                formData.delete('repeat_start');
                formData.delete('repeat_end');
            }

            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                console.log('[bindTaskFormHandler] Task added:', data);
                if (data.status === 'success' && data.day) {
                    fetch(`/tasks/${year}/${month}/${data.day}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(response => response.json())
                    .then(tasksData => {
                        updateTasksSection(tasksData.tasks, `${year}-${month}-${data.day}`, data.day, tasksData.categories || []);
                        updateCalendar(year, month); // Обновляем календарь
                    });
                }
            })
            .catch(error => {
                console.error('[bindTaskFormHandler] Error adding task:', error);
            });
        });
    }
}

function bindEditHandlers(year, month) {
    document.querySelectorAll('.edit-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            console.log(`[bindEditHandlers] Edit button clicked for task ${taskId}`);
            const editForm = document.getElementById(`edit-form-${taskId}`);
            if (editForm) {
                editForm.classList.toggle('active');
            }
        });
    });

    document.querySelectorAll('.cancel-edit').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            console.log(`[bindEditHandlers] Cancel edit for task ${taskId}`);
            const editForm = document.getElementById(`edit-form-${taskId}`);
            if (editForm) {
                editForm.classList.remove('active');
            }
        });
    });

    document.querySelectorAll('.edit-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('[bindEditHandlers] Edit form submitted');

            const formData = new FormData(this);
            const repeatEnabled = formData.get('repeat_enabled') === 'on';
            if (!repeatEnabled) {
                formData.delete('repeat_days');
                formData.delete('repeat_start');
                formData.delete('repeat_end');
            }

            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                console.log('[bindEditHandlers] Task updated:', data);
                if (data.status === 'success' && data.day) {
                    fetch(`/tasks/${year}/${month}/${data.day}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(response => response.json())
                    .then(tasksData => {
                        updateTasksSection(tasksData.tasks, `${year}-${month}-${data.day}`, data.day, tasksData.categories || []);
                        updateCalendar(year, month); // Обновляем календарь
                    });
                }
            })
            .catch(error => {
                console.error('[bindEditHandlers] Error updating task:', error);
            });
        });
    });
}

function bindDeleteHandlers(year, month) {
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            console.log(`[bindDeleteHandlers] Delete button clicked for task ${taskId}`);

            // Извлекаем текущий день из заголовка даты
            const currentDay = document.querySelector('.task-date-header')?.textContent.split('.')[0] || '01';

            fetch(`/tasks/${year}/${month}/${currentDay}`, { // Используем маршрут с day
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded', // Изменяем тип для совместимости с form
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: `delete=${taskId}` // Формируем тело как в форме
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                console.log('[bindDeleteHandlers] Delete response:', data);
                if (data.status === 'success' && data.day) {
                    fetch(`/tasks/${year}/${month}/${data.day}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(response => response.json())
                    .then(tasksData => {
                        updateTasksSection(tasksData.tasks, `${year}-${month}-${data.day}`, data.day, tasksData.categories || []);
                        updateCalendar(year, month); // Обновляем календарь
                    });
                }
            })
            .catch(error => {
                console.error('[bindDeleteHandlers] Error deleting task:', error);
            });
        });
    });
}

function bindCompleteHandlers(year, month) {
    document.querySelectorAll('.complete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            console.log(`[bindCompleteHandlers] Complete button clicked for task ${taskId}`);

            const currentDay = document.querySelector('.task-date-header')?.textContent.split('.')[0] || '01';

            fetch(`/tasks/${year}/${month}/${currentDay}/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ task_id: taskId })
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                console.log('[bindCompleteHandlers] Complete response:', data);
                if (data.success && data.day) {
                    fetch(`/tasks/${year}/${month}/${data.day}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(response => response.json())
                    .then(tasksData => {
                        updateTasksSection(tasksData.tasks, `${year}-${month}-${data.day}`, data.day, tasksData.categories || []);
                        fetchCompletedTasks(year, month, data.day);
                        updateCalendar(year, month); // Обновляем календарь
                    });
                }
            })
            .catch(error => {
                console.error('[bindCompleteHandlers] Error completing task:', error);
            });
        });
    });
}