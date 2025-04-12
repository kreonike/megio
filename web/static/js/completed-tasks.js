// completed-tasks.js

// Импортируем необходимые функции
import { fetchTasks } from './tasks.js';
import { updateTasksSection, updateCalendar } from './calendar-update.js';

// Обновляет секцию выполненных задач в интерфейсе
export function updateCompletedTasksSection(completedTasks, year, month, day) {
    console.log('[updateCompletedTasksSection] Updating completed tasks section');
    console.log('[updateCompletedTasksSection] Received completed tasks:', completedTasks);

    const completedSection = document.querySelector('.completed-tasks-section');
    if (!completedSection) {
        console.error('[updateCompletedTasksSection] Completed tasks section not found');
        return;
    }

    completedSection.innerHTML = `
        <h4 class="completed-tasks-header">Выполненные задачи</h4>
        <ul class="completed-tasks-list">
            ${!completedTasks || completedTasks.length === 0 ?
                '<li class="no-completed-tasks">Нет выполненных задач</li>' :
                completedTasks.map(task => `
                    <li class="completed-task-item" data-completed-task-id="${task.id}">
                        <div class="completed-task-content">
                            <span class="completed-task-text">${task.task_text}</span>
                            <span class="completed-time">${task.completion_time}</span>
                        </div>
                        <div class="completed-task-meta">
                            ${task.priority ?
                                `<span class="priority-indicator priority-${task.priority}">
                                    ${task.priority === 3 ? 'Высокий' : task.priority === 2 ? 'Средний' : 'Низкий'}
                                </span>` : ''
                            }
                            ${task.categories && Array.isArray(task.categories) ?
                                task.categories.map(cat => `
                                    <span class="category-tag" style="background-color: ${cat.color || '#ccc'}">
                                        ${cat.name || 'Без названия'}
                                    </span>
                                `).join('') : ''
                            }
                        </div>
                        <div class="completed-task-actions">
                            <button type="button" class="restore-btn" data-completed-task-id="${task.id}">Вернуть</button>
                        </div>
                    </li>
                `).join('')
            }
        </ul>
    `;

    // Привязываем обработчики для кнопок "Вернуть"
    document.querySelectorAll('.restore-btn').forEach(button => {
        button.addEventListener('click', function() {
            const completedTaskId = this.getAttribute('data-completed-task-id');
            console.log(`[updateCompletedTasksSection] Restore button clicked, completedTaskId: ${completedTaskId}`);
            if (completedTaskId) {
                restoreTask(completedTaskId, year, month, day);
            } else {
                console.error('[updateCompletedTasksSection] No completedTaskId found on button');
            }
        });
    });
}

// Загружает список выполненных задач с сервера
export function fetchCompletedTasks(year, month, day) {
    console.log(`[fetchCompletedTasks] Fetching completed tasks for ${year}-${month}-${day}`);
    return fetch(`/tasks/${year}/${month}/${day}/completed`, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        console.log('[fetchCompletedTasks] Response status:', response.status);
        if (!response.ok) {
            console.error('[fetchCompletedTasks] Network response not ok:', response.status);
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('[fetchCompletedTasks] Response data:', data);
        if (data.success && data.data) {
            updateCompletedTasksSection(data.data.completed_tasks || [], year, month, day);
        } else {
            console.error('[fetchCompletedTasks] Invalid response data:', data);
            updateCompletedTasksSection([], year, month, day);
            alert('Ошибка: сервер вернул некорректные данные о выполненных задачах');
        }
    })
    .catch(error => {
        console.error('[fetchCompletedTasks] Error fetching completed tasks:', error);
        updateCompletedTasksSection([], year, month, day);
        alert('Ошибка при загрузке выполненных задач: ' + error.message);
    });
}

// Восстанавливает выполненную задачу
function restoreTask(completedTaskId, year, month, day) {
    console.log(`[restoreTask] Restoring task with ID ${completedTaskId}`);
    fetch(`/tasks/${year}/${month}/${day}/restore`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ completed_task_id: completedTaskId })
    })
    .then(response => {
        console.log('[restoreTask] Response status:', response.status);
        if (!response.ok) {
            console.error('[restoreTask] Network response not ok:', response.status);
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('[restoreTask] Response data:', data);
        if (data.success) {
            console.log('[restoreTask] Task restored successfully');
            // Обновляем список активных задач и передаем fetchCompletedTasks как callback
            fetchTasks(year, month, day, fetchCompletedTasks);
            // Обновляем календарь
            updateCalendar(year, month);
        } else {
            console.error('[restoreTask] Error:', data.error);
            alert('Ошибка при восстановлении задачи: ' + (data.error || 'Неизвестная ошибка'));
        }
    })
    .catch(error => {
        console.error('[restoreTask] Error restoring task:', error);
        alert('Ошибка при восстановлении задачи: ' + error.message);
    });
}