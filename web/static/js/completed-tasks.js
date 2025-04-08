// static/js/completed-tasks.js
export function updateCompletedTasksSection(completedTasks, year, month, day) {
    console.log('[updateCompletedTasksSection] Updating completed tasks section');
    const taskList = document.querySelector('.task-list');
    if (!taskList) {
        console.log('[updateCompletedTasksSection] Task list not found');
        return;
    }

    let completedSection = taskList.querySelector('.completed-tasks-section');
    if (!completedSection) {
        completedSection = document.createElement('div');
        completedSection.className = 'completed-tasks-section';
        taskList.appendChild(completedSection);
    }

    completedSection.innerHTML = `
        <h4 class="completed-tasks-header">Выполненные задачи</h4>
        <ul class="completed-tasks-list">
            ${completedTasks.length === 0 ?
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
                            ${task.categories ?
                                `<span class="completed-categories">${task.categories}</span>` : ''
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

export function fetchCompletedTasks(year, month, day) {
    console.log(`[fetchCompletedTasks] Fetching completed tasks for ${year}-${month}-${day}`);
    return fetch(`/tasks/${year}/${month}/${day}/completed`, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        if (!response.ok) {
            console.error('[fetchCompletedTasks] Network response not ok:', response.status);
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('[fetchCompletedTasks] Received completed tasks:', JSON.stringify(data, null, 2));
        updateCompletedTasksSection(data.completed_tasks, year, month, day);
    })
    .catch(error => {
        console.error('[fetchCompletedTasks] Error fetching completed tasks:', error);
    });
}

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
        if (!response.ok) {
            console.error('[restoreTask] Network response not ok:', response.status);
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('[restoreTask] Task restored successfully');
            // Обновляем список активных задач
            fetch(`/tasks/${year}/${month}/${day}`, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json())
            .then(tasksData => {
                import('./calendar-update.js').then(module => {
                    module.updateTasksSection(tasksData.tasks, `${year}-${month}-${day}`, day, tasksData.categories || []);
                });
            });
            // Обновляем список выполненных задач
            fetchCompletedTasks(year, month, day);
        } else {
            console.error('[restoreTask] Failed to restore task:', data.error);
        }
    })
    .catch(error => {
        console.error('[restoreTask] Error restoring task:', error);
    });
}