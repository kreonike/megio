import {
    formatDateToRussian,
    formatDateForInput,
    bindTimeSpinnerEvents
} from "./time.js";
import { fetchCompletedTasks } from './completed-tasks.js';

export function updateTasksSection(tasks, completedTasks, date, day, categories) {
    console.log(`[updateTasksSection] Updating tasks for ${date}`, { tasks, completedTasks });
    const tasksSection = document.querySelector('.tasks-section');
    if (!tasksSection) {
        console.error('[updateTasksSection] Tasks section not found in DOM');
        return;
    }

    const dateParts = date.split('-');
    const year = dateParts[0];
    const month = dateParts[1];
    const dayNum = dateParts[2];
    const formattedDate = `${dayNum.padStart(2, '0')}.${month.padStart(2, '0')}.${year}`;

    // Фильтрация и сортировка завершённых задач
    const validCompletedTasks = completedTasks
        .filter(task => task.id && task.task_text)
        .sort((a, b) => new Date(b.completion_time) - new Date(a.completion_time));

    tasksSection.innerHTML = `
        <div class="calendar-filters">
            <select id="category-filter">
                <option value="">Все категории</option>
                ${categories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('')}
            </select>
            <select id="priority-filter">
                <option value="">Все приоритеты</option>
                <option value="3">Высокий</option>
                <option value="2">Средний</option>
                <option value="1">Низкий</option>
            </select>
        </div>
        <h3 class="task-date-header">${formattedDate}</h3>
        <form class="task-form" method="POST" action="/tasks/${year}/${month}/${day}">
            <input type="hidden" name="date" value="${date}">
            <input type="text" name="task" class="task-input" placeholder="Добавить новую задачу..." required>
            <div class="time-selector">
                <input type="text" id="task-time" name="time" class="time-input" value="12:00"
                       pattern="[0-9]{2}:[0-9]{2}" title="Формат: ЧЧ:ММ (24 часа)">
                <div class="time-spinner">
                    <button type="button" class="time-btn up">▲</button>
                    <button type="button" class="time-btn down">▼</button>
                </div>
            </div>
            <div class="task-priority">
                <label>Приоритет:</label>
                <select name="priority" id="task-priority-select">
                    <option value="1">Низкий</option>
                    <option value="2">Средний</option>
                    <option value="3">Высокий</option>
                </select>
            </div>
            <div class="task-categories">
                <label>Категории:</label>
                <div class="category-options">
                    ${categories.map(cat => `
                        <label>
                            <input type="checkbox" name="categories" value="${cat.id}">
                            <span class="category-badge" style="background-color: ${cat.color}">${cat.name}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
            <div class="repeat-options">
                <label>
                    <input type="checkbox" name="repeat_enabled" id="main-repeat-checkbox">
                    Повторять задачу
                </label>
                <div class="repeat-details" style="display: none;">
                    <div>
                        <span>Каждые</span>
                        <input type="number" name="repeat_days" min="1" max="365" value="1" style="width: 50px;">
                        <span>дней</span>
                    </div>
                    <div>
                        <span>Начиная с</span>
                        <input type="date" name="repeat_start" value="${date}">
                    </div>
                    <div>
                        <span>Заканчивая</span>
                        <input type="date" name="repeat_end">
                    </div>
                </div>
            </div>
            <button type="submit" class="task-button">Добавить задачу</button>
        </form>
        <h4 class="active-tasks-header">Активные задачи</h4>
        <ul class="task-list">
            ${tasks.length === 0 ? '<li class="no-tasks">Нет задач</li>' : tasks.map(task => `
                <li class="task-item" data-priority="${task.priority}" data-categories="${task.category_ids ? task.category_ids.join(',') : ''}">
                    <div class="task-content">
                        ${task.time ? `<span class="task-time">${task.time}</span>` : ''}
                        <span class="priority-marker"></span>
                        <span class="task-text">${task.task}</span>
                        ${task.repeat_days ? `<span class="task-repeat-badge">🔁 Каждые ${task.repeat_days} дней</span>` : ''}
                    </div>
                    <div class="task-meta">
                        <span class="priority-indicator priority-${task.priority}">
                            ${task.priority == 3 ? '❗ Высокий приоритет' :
                              task.priority == 2 ? '🔹 Средний приоритет' :
                              '🔸 Низкий приоритет'}
                        </span>
                        ${task.category_ids ? task.category_ids.map(cat_id => {
                            const cat = categories.find(c => c.id == cat_id);
                            return cat ? `<span class="category-tag" style="background-color: ${cat.color}">${cat.name}</span>` : '';
                        }).join('') : ''}
                    </div>
                    <div class="task-actions">
                        <button type="button" class="remind-btn" data-task-id="${task.id}">Напомнить</button>
                        <button type="button" class="edit-btn" data-task-id="${task.id}">Редактировать</button>
                        <button type="button" class="complete-btn" data-task-id="${task.id}">Выполнено</button>
                        <button type="button" class="delete-btn" data-task-id="${task.id}">Удалить</button>
                    </div>
                    <div id="remind-form-${task.id}" class="remind-form">
                        <div class="remind-options">
                            <label class="remind-option">
                                <input type="checkbox" name="remind_times" value="15" checked>
                                <span>За 15 минут</span>
                            </label>
                            <label class="remind-option">
                                <input type="checkbox" name="remind_times" value="120" checked>
                                <span>За 2 часа</span>
                            </label>
                            <label class="remind-option">
                                <input type="checkbox" name="remind_times" value="1440" checked>
                                <span>За 1 день</span>
                            </label>
                        </div>
                        <div class="remind-buttons">
                            <button type="button" class="remind-confirm-btn" data-task-id="${task.id}">Подтвердить</button>
                            <button type="button" class="cancel-remind">Отмена</button>
                        </div>
                    </div>
                    <form id="edit-form-${task.id}" class="edit-form" method="POST" action="/tasks/${year}/${month}/${day}">
                        <input type="hidden" name="task_id" value="${task.id}">
                        <input type="text" name="task" class="task-input" value="${task.task}" required>
                        <div class="time-selector">
                            <input type="text" name="time" class="edit-time-input" value="${task.time || '12:00'}"
                                   pattern="[0-9]{2}:[0-9]{2}">
                            <div class="time-spinner">
                                <button type="button" class="time-btn up">▲</button>
                                <button type="button" class="time-btn down">▼</button>
                            </div>
                        </div>
                        <div class="task-priority">
                            <label>Приоритет:</label>
                            <select name="priority">
                                <option value="1" ${task.priority == 1 ? 'selected' : ''}>Низкий</option>
                                <option value="2" ${task.priority == 2 ? 'selected' : ''}>Средний</option>
                                <option value="3" ${task.priority == 3 ? 'selected' : ''}>Высокий</option>
                            </select>
                        </div>
                        <div class="task-categories">
                            <label>Категории:</label>
                            <div class="category-options">
                                ${categories.map(cat => `
                                    <label>
                                        <input type="checkbox" name="categories" value="${cat.id}"
                                               ${task.category_ids && task.category_ids.includes(cat.id) ? 'checked' : ''}>
                                        <span class="category-badge" style="background-color: ${cat.color}">${cat.name}</span>
                                    </label>
                                `).join('')}
                            </div>
                        </div>
                        <div class="repeat-options">
                            <label>
                                <input type="checkbox" name="repeat_enabled" class="edit-repeat-checkbox"
                                    ${task.repeat_days !== null && task.repeat_days > 0 ? 'checked' : ''}>
                                Повторять задачу
                            </label>
                            <div class="repeat-details" style="${task.repeat_days !== null && task.repeat_days > 0 ? 'display: block;' : 'display: none;'}">
                                <div>
                                    <span>Каждые</span>
                                    <input type="number" name="repeat_days" min="1" max="365"
                                        value="${task.repeat_days || 1}" style="width: 50px;">
                                    <span>дней</span>
                                </div>
                                <div>
                                    <span>Начиная с</span>
                                    <input type="date" name="repeat_start"
                                        value="${formatDateForInput(task.repeat_start || date)}">
                                </div>
                                <div>
                                    <span>Заканчивая</span>
                                    <input type="date" name="repeat_end"
                                        value="${formatDateForInput(task.repeat_end || '')}">
                                </div>
                            </div>
                        </div>
                        <div class="edit-buttons">
                            <button type="submit" class="task-button">Сохранить</button>
                            <button type="button" class="cancel-edit" data-task-id="${task.id}">Отмена</button>
                        </div>
                    </form>
                </li>
            `).join('')}
        </ul>
        <h4 class="completed-tasks-header">Завершённые задачи</h4>
        <ul class="completed-task-list">
            ${validCompletedTasks.length === 0 ? '<li class="no-completed-tasks">Нет завершённых задач</li>' : validCompletedTasks.map(task => `
                <li class="completed-task-item" data-task-id="${task.id}" data-priority="${task.priority}">
                    <div class="completed-task-content">
                        <span class="completed-task-text">${task.task_text}</span>
                    </div>
                    <div class="completed-task-meta">
                        ${task.completion_time ? `<span class="completed-time">Завершено: ${formatCompletionTime(task.completion_time)}</span>` : ''}
                        <span class="priority-indicator priority-${task.priority}">
                            ${task.priority == 3 ? '❗ Высокий приоритет' :
                              task.priority == 2 ? '🔹 Средний приоритет' :
                              '🔸 Низкий приоритет'}
                        </span>
                        ${task.categories ? task.categories.split(',').map(cat_id => {
                            const cat = categories.find(c => c.id == parseInt(cat_id));
                            return cat ? `<span class="category-tag" style="background-color: ${cat.color}">${cat.name}</span>` : '';
                        }).filter(tag => tag).join('') : ''}
                    </div>
                    <button type="button" class="restore-btn" data-task-id="${task.id}">Восстановить</button>
                </li>
            `).join('')}
        </ul>
    `;

    const yearNum = parseInt(year);
    const monthNum = parseInt(month);
    bindAllTaskHandlers(yearNum, monthNum, day);

    document.querySelectorAll('.edit-time-input').forEach(input => {
        bindTimeSpinnerEvents(input);
    });

    const taskTimeInput = document.getElementById('task-time');
    if (taskTimeInput) {
        bindTimeSpinnerEvents(taskTimeInput);
    }

    const mainRepeatCheckbox = document.getElementById('main-repeat-checkbox');
    if (mainRepeatCheckbox) {
        mainRepeatCheckbox.addEventListener('change', function(e) {
            e.stopPropagation();
            const details = this.closest('.repeat-options').querySelector('.repeat-details');
            if (details) {
                details.style.display = this.checked ? 'block' : 'none';
                if (!this.checked) {
                    details.querySelector('input[name="repeat_days"]').value = '1';
                    details.querySelector('input[name="repeat_start"]').value = date;
                    details.querySelector('input[name="repeat_end"]').value = '';
                }
            }
        });
    }

    document.querySelectorAll('.edit-repeat-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function(e) {
            e.stopPropagation();
            const details = this.closest('.repeat-options').querySelector('.repeat-details');
            if (details) {
                details.style.display = this.checked ? 'block' : 'none';
                if (!this.checked) {
                    details.querySelector('input[name="repeat_days"]').value = '1';
                    const dateInput = details.querySelector('input[name="repeat_start"]');
                    dateInput.value = formatDateForInput(new Date());
                    details.querySelector('input[name="repeat_end"]').value = '';
                }
            }
        });
    });

    document.getElementById('category-filter')?.addEventListener('change', applyFilters);
    document.getElementById('priority-filter')?.addEventListener('change', applyFilters);

    document.querySelectorAll('.restore-btn').forEach(button => {
        button.removeEventListener('click', handleRestore);
        button.addEventListener('click', handleRestore);
    });

    function handleRestore(e) {
        e.preventDefault();
        const button = e.target;
        const taskId = button.getAttribute('data-task-id');
        console.log(`[handleRestore] Restoring task ${taskId} for ${year}-${month}-${day}`);

        if (!taskId) {
            console.error('[handleRestore] No taskId found');
            alert('Ошибка: ID задачи не найден');
            return;
        }

        fetch(`/tasks/${year}/${month}/${day}/restore`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ completed_task_id: taskId })
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Задача не найдена в завершённых');
                } else if (response.status === 409) {
                    throw new Error('Задача уже восстановлена');
                }
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log(`[handleRestore] Task ${taskId} restored`);
                Promise.all([
                    fetch(`/tasks/${year}/${month}/${day}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    }).then(res => res.json()),
                    fetchCompletedTasks(year, month, day)
                ]).then(([taskData, completedTasks]) => {
                    if (taskData.success && taskData.data) {
                        updateTasksSection(
                            taskData.data.tasks || [],
                            completedTasks,
                            `${year}-${month}-${day}`,
                            day,
                            taskData.data.categories || []
                        );
                        updateCalendar(year, month);
                    } else {
                        console.error('[handleRestore] Invalid task data:', taskData);
                        alert('Ошибка: некорректные данные после восстановления');
                    }
                }).catch(error => {
                    console.error('[handleRestore] Error refreshing tasks:', error);
                    alert('Ошибка при обновлении задач: ' + error.message);
                });
            } else {
                console.error('[handleRestore] Restore failed:', data.error);
                alert('Ошибка при восстановлении задачи: ' + (data.error || 'Неизвестная ошибка'));
            }
        })
        .catch(error => {
            console.error('[handleRestore] Error:', error);
            alert('Ошибка при восстановлении задачи: ' + error.message);
        });
    }
}

function applyFilters() {
    const categoryFilter = document.getElementById('category-filter')?.value;
    const priorityFilter = document.getElementById('priority-filter')?.value;

    document.querySelectorAll('.task-item, .completed-task-item').forEach(item => {
        const itemCategories = item.dataset.categories ? item.dataset.categories.split(',') : [];
        const itemPriority = item.dataset.priority;
        const categoryMatch = !categoryFilter || itemCategories.includes(categoryFilter);
        const priorityMatch = !priorityFilter || itemPriority === priorityFilter;
        item.style.display = (categoryMatch && priorityMatch) ? '' : 'none';
    });
}

function formatCompletionTime(timestamp) {
    try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
        console.warn('[formatCompletionTime] Invalid timestamp:', timestamp);
        return '';
    }
}

export function updateCalendar(year, month) {
    console.log(`[updateCalendar] Updating for ${year}-${month}`);
    document.querySelectorAll('.task-count-badge').forEach(badge => {
        badge.classList.add('updating');
    });

    return fetch(`/tasks/${year}/${month}`, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        if (!response.ok) throw new Error(`Network response was not ok: ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log(`[updateCalendar] Received data for ${year}-${month}`, data);
        if (!data.success || !data.data) throw new Error('Invalid response data');
        const tasksByDay = data.data.tasksByDay || {};
        console.log(`[updateCalendar] tasksByDay`, tasksByDay);

        const promises = [];
        for (let day = 1; day <= 31; day++) {
            promises.push(
                fetchCompletedTasks(year, month, day)
                    .then(completedTasks => ({ day, completedTasks: completedTasks || [] }))
                    .catch(err => {
                        console.error(`[updateCalendar] Error fetching completed tasks for day ${day}:`, err);
                        return { day, completedTasks: [] };
                    })
            );
        }

        return Promise.all(promises).then(completedResults => {
            const completedTasksByDay = {};
            completedResults.forEach(result => {
                completedTasksByDay[result.day] = result.completedTasks;
            });
            console.log(`[updateCalendar] completedTasksByDay`, completedTasksByDay);

            document.querySelectorAll('.day-link').forEach(link => {
                const day = link.getAttribute('data-day');
                const dayCell = link.closest('.day-cell');
                let badge = link.querySelector('.task-count-badge');

                if (day) {
                    const tasks = tasksByDay[day] || [];
                    const completedTasks = completedTasksByDay[day] || [];
                    console.log(`[updateCalendar] Processing day ${day}`, { tasks, completedTasks });

                    dayCell.classList.remove('has-overdue-tasks', 'all-tasks-completed', 'has-tasks');

                    const allTasks = [...tasks, ...completedTasks.map(task => ({
                        ...task,
                        completed: 1,
                        priority: task.priority || 1
                    }))];

                    if (allTasks.length > 0) {
                        const now = new Date();
                        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                        const taskDate = new Date(year, month - 1, day);

                        let hasOverdue = false;
                        let allCompleted = allTasks.length > 0;
                        let maxPriority = 1;
                        let hasIncompleteTasks = false;

                        allTasks.forEach(task => {
                            if (taskDate < today && !task.completed) hasOverdue = true;
                            if (!task.completed) {
                                allCompleted = false;
                                hasIncompleteTasks = true;
                            }
                            maxPriority = Math.max(maxPriority, task.priority || 1);
                        });

                        if (hasIncompleteTasks) {
                            dayCell.classList.add('has-tasks');
                            if (!badge) {
                                badge = document.createElement('span');
                                badge.className = 'task-count-badge';
                                link.appendChild(badge);
                            }
                            badge.textContent = allTasks.filter(task => !task.completed).length;
                            badge.classList.remove('priority-low', 'priority-medium', 'priority-high');
                            if (maxPriority === 3) {
                                badge.classList.add('priority-high');
                            } else if (maxPriority === 2) {
                                badge.classList.add('priority-medium');
                            } else {
                                badge.classList.add('priority-low');
                            }
                        } else {
                            if (badge) badge.remove();
                        }

                        if (hasOverdue) {
                            dayCell.classList.add('has-overdue-tasks');
                        } else if (allCompleted && allTasks.length > 0) {
                            dayCell.classList.add('all-tasks-completed');
                        }
                    } else {
                        if (badge) badge.remove();
                        dayCell.classList.remove('has-tasks');
                    }
                }
            });
        });
    })
    .catch(error => {
        console.error('[updateCalendar] Error:', error);
        alert('Ошибка при обновлении календаря: ' + error.message);
        throw error;
    })
    .finally(() => {
        document.querySelectorAll('.task-count-badge').forEach(badge => {
            badge.classList.remove('updating');
        });
    });
}

export function updateTaskPriorityIndicator(dayElement, tasks, completedTasks) {
    console.log(`[updateTaskPriorityIndicator] Updating for dayElement`, { tasks, completedTasks });
    const badge = dayElement.querySelector('.task-count-badge');
    const allTasks = [...(tasks || []), ...(completedTasks || []).map(task => ({
        ...task,
        priority: task.priority || 1,
        completed: 1
    }))];

    if (allTasks.length === 0) {
        dayElement.classList.remove('has-tasks', 'has-overdue-tasks', 'all-tasks-completed');
        if (badge) badge.remove();
        return;
    }

    const hasIncompleteTasks = tasks.some(task => !task.completed);

    if (hasIncompleteTasks) {
        if (!badge) {
            const link = dayElement.querySelector('.day-link');
            if (link) {
                const newBadge = document.createElement('span');
                newBadge.className = 'task-count-badge';
                link.appendChild(newBadge);
            }
        }

        const updatedBadge = dayElement.querySelector('.task-count-badge');
        if (updatedBadge) {
            let maxPriority = 1;
            tasks.forEach(task => {
                if (!task.completed) {
                    maxPriority = Math.max(maxPriority, task.priority || 1);
                }
            });

            updatedBadge.textContent = tasks.filter(task => !task.completed).length;
            updatedBadge.classList.remove('priority-low', 'priority-medium', 'priority-high');
            if (maxPriority === 3) updatedBadge.classList.add('priority-high');
            else if (maxPriority === 2) updatedBadge.classList.add('priority-medium');
            else updatedBadge.classList.add('priority-low');
        }
        dayElement.classList.add('has-tasks');
    } else {
        if (badge) badge.remove();
        dayElement.classList.remove('has-tasks');
        if (allTasks.length > 0) {
            dayElement.classList.add('all-tasks-completed');
        }
    }
}

export function bindAllTaskHandlers(year, month, day) {
    console.log(`[bindAllTaskHandlers] Binding handlers for ${year}-${month}-${day}`);
    const links = document.querySelectorAll('.day-link');
    links.forEach(link => {
        link.removeEventListener('click', handleDayClick);
        link.addEventListener('click', handleDayClick);
    });

    function handleDayClick(e) {
        e.preventDefault();
        document.querySelectorAll('.day-link').forEach(l => l.classList.remove('selected'));
        this.classList.add('selected');
        const dayAttr = this.getAttribute('data-day');
        if (!dayAttr || isNaN(dayAttr)) {
            console.error('[handleDayClick] Invalid day attribute:', dayAttr);
            return;
        }

        const date = `${year}-${String(month).padStart(2, '0')}-${String(dayAttr).padStart(2, '0')}`;
        console.log('[handleDayClick] Fetching tasks for:', date);

        const tasksSection = document.querySelector('.tasks-section');
        if (tasksSection) tasksSection.innerHTML = '<p>Загрузка...</p>';

        Promise.all([
            fetch(`/tasks/${year}/${month}/${dayAttr}`, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            }).then(response => {
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            }),
            fetchCompletedTasks(year, month, dayAttr)
        ])
        .then(([taskData, completedTasks]) => {
            console.log('[handleDayClick] Task data received:', taskData, completedTasks);
            if (taskData.success && taskData.data) {
                updateTasksSection(
                    taskData.data.tasks || [],
                    completedTasks || [],
                    date,
                    dayAttr,
                    taskData.data.categories || []
                );
                updateTaskPriorityIndicator(
                    this.closest('.day-cell'),
                    taskData.data.tasks || [],
                    completedTasks || []
                );
            } else {
                console.error('[handleDayClick] Invalid task response data:', taskData);
                alert('Ошибка: некорректные данные');
                if (tasksSection) tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
            }
        })
        .catch(error => {
            console.error('[handleDayClick] Error loading tasks:', error);
            alert('Ошибка при загрузке задач: ' + error.message);
            if (tasksSection) tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
        });
    }

    document.querySelectorAll('.remind-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const taskId = this.getAttribute('data-task-id');
            const remindForm = document.getElementById(`remind-form-${taskId}`);
            document.querySelectorAll('.remind-form.active, .edit-form.active').forEach(form => {
                if (form !== remindForm) form.classList.remove('active');
            });
            remindForm.classList.toggle('active');
        });
    });

    document.querySelectorAll('.remind-confirm-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            const remindForm = this.closest('.remind-form');
            const selectedReminders = Array.from(
                remindForm.querySelectorAll('input[name="remind_times"]:checked')
            ).map(el => parseInt(el.value));

            if (selectedReminders.length === 0) {
                alert('Выберите хотя бы одно время напоминания');
                return;
            }

            fetch(`/tasks/${year}/${month}/${day}/remind`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    task_id: taskId,
                    remind_times: selectedReminders
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    remindForm.classList.remove('active');
                    console.log('[remind] Reminders set for task', taskId);
                } else {
                    console.error('[remind] Error setting reminders:', data.error);
                    alert('Ошибка при установке напоминаний: ' + data.error);
                }
            })
            .catch(error => {
                console.error('[remind] Error:', error);
                alert('Ошибка при отправке запроса');
            });
        });
    });

    document.querySelectorAll('.cancel-remind').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.remind-form').classList.remove('active');
        });
    });

    document.querySelectorAll('.edit-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const taskId = this.getAttribute('data-task-id');
            const editForm = document.getElementById(`edit-form-${taskId}`);
            document.querySelectorAll('.edit-form.active, .remind-form.active').forEach(form => {
                if (form !== editForm) form.classList.remove('active');
            });
            editForm.classList.toggle('active');
        });
    });

    document.querySelectorAll('.cancel-edit').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.edit-form').classList.remove('active');
        });
    });

    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            if (!confirm('Вы уверены, что хотите удалить эту задачу?')) return;
            const taskId = this.getAttribute('data-task-id');

            fetch(`/tasks/${year}/${month}/${day}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: `delete=${taskId}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Promise.all([
                        fetch(`/tasks/${year}/${month}/${day}`, {
                            method: 'GET',
                            headers: { 'X-Requested-With': 'XMLHttpRequest' }
                        }).then(res => res.json()),
                        fetchCompletedTasks(year, month, day)
                    ]).then(([taskData, completedTasks]) => {
                        if (taskData.success && taskData.data) {
                            updateTasksSection(
                                taskData.data.tasks || [],
                                completedTasks || [],
                                `${year}-${month}-${day}`,
                                day,
                                taskData.data.categories || []
                            );
                            updateCalendar(year, month);
                        }
                    });
                } else {
                    alert('Ошибка при удалении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('[delete] Error:', error);
                alert('Ошибка при удалении задачи');
            });
        });
    });

    document.querySelectorAll('.complete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');

            fetch(`/tasks/${year}/${month}/${day}/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ task_id: taskId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Promise.all([
                        fetch(`/tasks/${year}/${month}/${day}`, {
                            method: 'GET',
                            headers: { 'X-Requested-With': 'XMLHttpRequest' }
                        }).then(res => res.json()),
                        fetchCompletedTasks(year, month, day)
                    ]).then(([taskData, completedTasks]) => {
                        if (taskData.success && taskData.data) {
                            updateTasksSection(
                                taskData.data.tasks || [],
                                completedTasks,
                                `${year}-${month}-${day}`,
                                day,
                                taskData.data.categories || []
                            );
                            updateCalendar(year, month);
                        }
                    });
                } else {
                    alert('Ошибка при выполнении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('[complete] Error:', error);
                alert('Ошибка при выполнении задачи');
            });
        });
    });

    document.querySelector('.task-form')?.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('[task-form] Submitting task form', new FormData(this));
        fetch(this.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: new FormData(this)
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('[task-form] Response:', data);
            if (data.success) {
                this.reset();
                Promise.all([
                    fetch(`/tasks/${year}/${month}/${day}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    }).then(res => res.json()),
                    fetchCompletedTasks(year, month, day)
                ]).then(([taskData, completedTasks]) => {
                    console.log('[task-form] Fetched tasks after add:', taskData, completedTasks);
                    if (taskData.success && taskData.data) {
                        updateTasksSection(
                            taskData.data.tasks || [],
                            completedTasks || [],
                            `${year}-${month}-${day}`,
                            day,
                            taskData.data.categories || []
                        );
                        updateCalendar(year, month);
                    } else {
                        console.error('[task-form] Invalid task data:', taskData);
                        alert('Ошибка при загрузке задач после добавления: ' + (taskData.error || 'Неизвестная ошибка'));
                    }
                }).catch(error => {
                    console.error('[task-form] Error fetching tasks:', error);
                    alert('Ошибка при обновлении задач: ' + error.message);
                });
            } else {
                console.error('[task-form] Server error:', data.error);
                alert('Ошибка при добавлении задачи: ' + (data.error || 'Неизвестная ошибка'));
            }
        })
        .catch(error => {
            console.error('[task-form] Network error:', error);
            alert('Ошибка при добавлении задачи: ' + error.message);
        });
    });

    document.querySelectorAll('.edit-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            fetch(this.action, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: new FormData(this)
            })
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    this.classList.remove('active');
                    Promise.all([
                        fetch(`/tasks/${year}/${month}/${day}`, {
                            method: 'GET',
                            headers: { 'X-Requested-With': 'XMLHttpRequest' }
                        }).then(res => res.json()),
                        fetchCompletedTasks(year, month, day)
                    ]).then(([taskData, completedTasks]) => {
                        if (taskData.success && taskData.data) {
                            updateTasksSection(
                                taskData.data.tasks || [],
                                completedTasks || [],
                                `${year}-${month}-${day}`,
                                day,
                                taskData.data.categories || []
                            );
                            updateCalendar(year, month).then(() => {
                                console.log(`[edit-form] Calendar updated after task edit for ${year}-${month}`);
                            }).catch(error => {
                                console.error('[edit-form] Error updating calendar:', error);
                            });
                        }
                    });
                } else {
                    alert('Ошибка при обновлении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('[edit-form] Error:', error);
                alert('Ошибка при обновлении задачи: ' + error.message);
            });
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth() + 1;
    const day = today.getDate();
    console.log(`[DOMContentLoaded] Initializing for ${year}-${month}-${day}`);
    bindAllTaskHandlers(year, month, day);
    updateCalendar(year, month);

    Promise.all([
        fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        }).then(response => response.json()),
        fetchCompletedTasks(year, month, day)
    ])
    .then(([taskData, completedTasks]) => {
        console.log('[DOMContentLoaded] Initial tasks:', taskData, completedTasks);
        if (taskData.success && taskData.data) {
            updateTasksSection(
                taskData.data.tasks || [],
                completedTasks || [],
                `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
                day,
                taskData.data.categories || []
            );
        }
    })
    .catch(error => console.error('[DOMContentLoaded] Error loading initial tasks:', error));
});