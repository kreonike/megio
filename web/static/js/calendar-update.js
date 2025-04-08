// static/js/calendar-update.js
import {
    formatDateToRussian,
    formatDateForInput,
    bindTimeSpinnerEvents
} from "./time.js";

import { bindAllTaskHandlers } from './tasks.js';
import { updateCompletedTasksSection, fetchCompletedTasks } from './completed-tasks.js';
import { bindRemindHandlers } from './remind.js';

export function updateTasksSection(tasks, date, day, categories) {
    console.log(`[updateTasksSection] Updating for date ${date}, day ${day}`);
    console.log(`[updateTasksSection] Received tasks:`, tasks);
    const dateParts = date.split('-');
    const year = dateParts[0];
    const month = dateParts[1];
    const dayNum = dateParts[2];
    const formattedDate = `${dayNum.padStart(2, '0')}.${month.padStart(2, '0')}.${year}`;

    const tasksSection = document.querySelector('.tasks-section');
    if (!tasksSection) {
        console.log('[updateTasksSection] Tasks section not found');
        return;
    }

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

        <h3 class="task-date-header" style="color: inherit;">${formattedDate}</h3>
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
            ${tasks.length === 0 ? '<li class="no-tasks">Нет задач</li>' : tasks.map(task => {
                console.log(`[updateTasksSection] Rendering task ${task.id} with repeat_days: ${task.repeat_days}`);
                return `
                    <li class="task-item" data-priority="${task.priority}" data-categories="${task.category_ids ? task.category_ids.join(',') : ''}">
                        <div class="task-content">
                            ${task.time ? `<span class="task-time">${task.time}</span>` : ''}
                            <span class="priority-marker"></span>
                            <span class="task-text">${task.task}</span>
                            ${task.repeat_days ? `<span class="task-repeat-badge">🔁 Каждые ${task.repeat_days} дней</span>` : ''}
                        </div>
                        <div class="task-meta">
                            ${task.priority == 3 ? '<span class="priority-high">❗ Высокий приоритет</span>' : ''}
                            ${task.priority == 2 ? '<span class="priority-medium">🔹 Средний приоритет</span>' : ''}
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
                        <form id="remind-form-${task.id}" class="remind-form" data-task-id="${task.id}">
                            <div class="remind-options">
                                <label class="remind-option">
                                    <input type="checkbox" name="remind-options" value="5"> За 5 минут
                                </label>
                                <label class="remind-option">
                                    <input type="checkbox" name="remind-options" value="15"> За 15 минут
                                </label>
                                <label class="remind-option">
                                    <input type="checkbox" name="remind-options" value="30"> За 30 минут
                                </label>
                                <label class="remind-option">
                                    <input type="checkbox" name="remind-options" value="60"> За 1 час
                                </label>
                            </div>
                            <div class="remind-buttons">
                                <button type="submit" class="remind-confirm-btn">Установить</button>
                                <button type="button" class="cancel-remind">Отмена</button>
                            </div>
                        </form>
                    </li>
                `;
            }).join('')}
        </ul>
    `;

    const dateHeader = tasksSection.querySelector('.task-date-header');
    if (dateHeader) {
        dateHeader.style.color = tasks.length > 0 ? '#ff9800' : 'inherit';
        console.log(`[updateTasksSection] Date header color set to: ${dateHeader.style.color}`);
    }

    const yearNum = parseInt(year);
    const monthNum = parseInt(month);

    bindAllTaskHandlers(yearNum, monthNum);
    bindRemindHandlers(yearNum, monthNum);

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
            console.log('[updateTasksSection] Main repeat checkbox changed');
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
            const taskId = this.closest('.edit-form').querySelector('input[name="task_id"]').value;
            console.log(`[updateTasksSection] Edit repeat checkbox changed for task ${taskId}, checked: ${this.checked}`);
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

    fetchCompletedTasks(yearNum, monthNum, day);
}

function applyFilters() {
    console.log('[applyFilters] Applying filters');
    const categoryFilter = document.getElementById('category-filter')?.value;
    const priorityFilter = document.getElementById('priority-filter')?.value;
    console.log(`[applyFilters] Category: ${categoryFilter}, Priority: ${priorityFilter}`);

    document.querySelectorAll('.task-item').forEach(item => {
        const itemCategories = item.dataset.categories ? item.dataset.categories.split(',') : [];
        const itemPriority = item.dataset.priority;

        const categoryMatch = !categoryFilter || itemCategories.includes(categoryFilter);
        const priorityMatch = !priorityFilter || itemPriority === priorityFilter;

        item.style.display = (categoryMatch && priorityMatch) ? '' : 'none';
    });
}

export function updateCalendar(year, month) {
    console.log(`[updateCalendar] Starting update for ${year}-${month}`);

    document.querySelectorAll('.task-count-badge').forEach(badge => {
        badge.classList.add('updating');
    });

    return fetch(`/tasks/${year}/${month}`, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        if (!response.ok) {
            console.error(`[updateCalendar] Network response not ok: ${response.status}`);
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log(`[updateCalendar] Received data:`, data);
        const calendarTable = document.querySelector('.calendar-table');
        if (!calendarTable) {
            console.error('[updateCalendar] Calendar table not found');
            return;
        }

        calendarTable.querySelectorAll('.day-link').forEach(link => {
            const day = link.getAttribute('data-day');
            console.log(`[updateCalendar] Processing day ${day}`);

            const dayCell = link.closest('.day-cell');
            if (!dayCell) {
                console.warn(`[updateCalendar] No day-cell found for day ${day}`);
                return;
            }

            let badge = link.querySelector('.task-count-badge');

            if (day && data.tasksByDay.hasOwnProperty(day)) {
                const tasks = data.tasksByDay[day];
                console.log(`[updateCalendar] Found ${tasks.length} tasks for day ${day}`);

                dayCell.classList.remove('has-overdue-tasks', 'all-tasks-completed');

                if (tasks.length > 0) {
                    const now = new Date();
                    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                    const taskDate = new Date(year, month - 1, day);

                    let hasOverdue = false;
                    let allCompleted = true;

                    tasks.forEach(task => {
                        if (taskDate < today && !task.completed) {
                            hasOverdue = true;
                        }
                        if (!task.completed) {
                            allCompleted = false;
                        }
                    });

                    if (hasOverdue) {
                        dayCell.classList.add('has-overdue-tasks');
                    } else if (allCompleted) {
                        dayCell.classList.add('all-tasks-completed');
                    }

                    if (!badge) {
                        console.log(`[updateCalendar] Creating new badge for day ${day}`);
                        badge = document.createElement('span');
                        badge.className = 'task-count-badge';
                        link.appendChild(badge);
                    }

                    let maxPriority = 1;
                    tasks.forEach(task => {
                        if (task.priority > maxPriority) maxPriority = task.priority;
                    });

                    badge.textContent = tasks.length;
                    badge.classList.remove('priority-low', 'priority-medium', 'priority-high');

                    if (maxPriority === 3) {
                        badge.classList.add('priority-high');
                    } else if (maxPriority === 2) {
                        badge.classList.add('priority-medium');
                    } else {
                        badge.classList.add('priority-low');
                    }

                    dayCell.classList.add('has-tasks');
                    console.log(`[updateCalendar] Updated badge for day ${day} with ${tasks.length} tasks`);
                } else {
                    if (badge) {
                        console.log(`[updateCalendar] Removing badge for day ${day} as no tasks remain`);
                        badge.remove();
                    }
                    dayCell.classList.remove('has-tasks');
                }
            } else {
                if (badge) {
                    console.log(`[updateCalendar] Removing badge for day ${day} as no tasks exist`);
                    badge.remove();
                }
                dayCell.classList.remove('has-tasks');
            }
        });
    })
    .catch(error => {
        console.error('[updateCalendar] Error updating calendar:', error);
        throw error;
    })
    .finally(() => {
        console.log('[updateCalendar] Finished updating calendar');
        document.querySelectorAll('.task-count-badge').forEach(badge => {
            badge.classList.remove('updating');
        });
    });
}

export function updateTaskPriorityIndicator(dayElement, tasks) {
    console.log(`[updateTaskPriorityIndicator] Updating for day element`, dayElement);
    const badge = dayElement.querySelector('.task-count-badge');
    if (!badge) {
        console.log('[updateTaskPriorityIndicator] No badge found');
        return;
    }
    if (!tasks || tasks.length === 0) {
        console.log('[updateTaskPriorityIndicator] No tasks provided');
        dayElement.classList.remove('has-tasks');
        badge.remove();
        return;
    }

    let maxPriority = 1;
    tasks.forEach(task => {
        if (task.priority > maxPriority) maxPriority = task.priority;
    });

    badge.classList.remove('priority-low', 'priority-medium', 'priority-high');

    if (maxPriority === 3) {
        badge.classList.add('priority-high');
    } else if (maxPriority === 2) {
        badge.classList.add('priority-medium');
    } else {
        badge.classList.add('priority-low');
    }

    console.log(`[updateTaskPriorityIndicator] Updated priority to ${maxPriority}`);
}