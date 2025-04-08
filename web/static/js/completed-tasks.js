// static/js/completed-tasks.js
export function updateCompletedTasksSection(completedTasks, year, month, day) {
    console.log('[updateCompletedTasksSection] Updating completed tasks section');
    const taskList = document.querySelector('.task-list');
    if (!taskList) {
        console.log('[updateCompletedTasksSection] Task list not found');
        return;
    }

    // Находим или создаем секцию выполненных задач
    let completedSection = taskList.querySelector('.completed-tasks-section');
    if (!completedSection) {
        completedSection = document.createElement('div');
        completedSection.className = 'completed-tasks-section';
        taskList.appendChild(completedSection);
    }

    // Формируем HTML для выполненных задач
    completedSection.innerHTML = `
        <h4 class="completed-tasks-header">Выполненные задачи</h4>
        <ul class="completed-tasks-list">
            ${completedTasks.length === 0 ?
                '<li class="no-completed-tasks">Нет выполненных задач</li>' :
                completedTasks.map(task => `
                    <li class="completed-task-item" data-task-id="${task.task_id}">
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
                    </li>
                `).join('')
            }
        </ul>
    `;
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
        console.log('[fetchCompletedTasks] Received completed tasks:', data);
        updateCompletedTasksSection(data.completed_tasks, year, month, day);
    })
    .catch(error => {
        console.error('[fetchCompletedTasks] Error fetching completed tasks:', error);
    });
}