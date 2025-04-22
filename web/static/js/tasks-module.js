import { formatDateToRussian, formatDateForInput, formatCompletionTime } from './utils.js';

export function updateTasksSection(tasks, completedTasks, date, day, categories) {
    console.log(`[tasks-module/updateTasksSection] Updating tasks for ${date}, tasks: ${tasks.length}, completed: ${completedTasks.length}, categories: ${categories.length}`);
    const tasksSection = document.querySelector('.tasks-section');
    if (!tasksSection) {
        console.error('[tasks-module/updateTasksSection] Tasks section not found in DOM');
        return;
    }

    const dateParts = date.split('-');
    const year = dateParts[0];
    const month = dateParts[1];
    const dayNum = dateParts[2];
    const formattedDate = `${dayNum.padStart(2, '0')}.${month.padStart(2, '0')}.${year}`;

    const validCompletedTasks = (completedTasks || [])
        .filter(task => task.id && task.task_text)
        .sort((a, b) => new Date(b.completion_time) - new Date(a.completion_time));

    const validTasks = (tasks || []).filter(task => task.id && task.task);
    const validCategories = (categories || []).filter(cat => cat.id && cat.name);

    tasksSection.innerHTML = `
        <div class="calendar-filters">
            <select id="category-filter">
                <option value="">Все категории</option>
                ${validCategories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('')}
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
                    <button type="button" class="time-btn up" aria-label="Увеличить время">▲</button>
                    <button type="button" class="time-btn down" aria-label="Уменьшить время">▼</button>
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
                    ${validCategories.length > 0 ?
                        validCategories.map(cat => `
                            <label class="category-option">
                                <input type="checkbox" name="categories" value="${cat.id}">
                                <span class="category-badge" style="background-color: ${cat.color || '#ccc'}">${cat.name}</span>
                            </label>
                        `).join('')
                        : '<p class="no-categories">Нет доступных категорий</p>'
                    }
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
            ${validTasks.length === 0 ? '<li class="no-tasks">Нет задач</li>' : validTasks.map(task => `
                <li class="task-item" data-priority="${task.priority || 1}" data-categories="${task.category_ids ? task.category_ids.join(',') : ''}">
                    <div class="task-content">
                        ${task.time ? `<span class="task-time">${task.time}</span>` : ''}
                        <span class="priority-marker"></span>
                        <span class="task-text">${task.task}</span>
                        ${task.repeat_days ? `<span class="task-repeat-badge">🔁 Каждые ${task.repeat_days} дней</span>` : ''}
                    </div>
                    <div class="task-meta">
                        <span class="priority-indicator priority-${task.priority || 1}">
                            ${task.priority == 3 ? '❗ Высокий приоритет' :
                              task.priority == 2 ? '🔹 Средний приоритет' :
                              '🔸 Низкий приоритет'}
                        </span>
                        ${task.category_ids ? task.category_ids.map(cat_id => {
                            const cat = validCategories.find(c => c.id == cat_id);
                            return cat ? `<span class="category-tag" style="background-color: ${cat.color || '#ccc'}">${cat.name}</span>` : '';
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
                                   pattern="[0-9]{2}:[0-9]{2}" title="Формат: ЧЧ:ММ">
                            <div class="time-spinner">
                                <button type="button" class="time-btn up" aria-label="Увеличить время">▲</button>
                                <button type="button" class="time-btn down" aria-label="Уменьшить время">▼</button>
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
                                ${validCategories.map(cat => `
                                    <label>
                                        <input type="checkbox" name="categories" value="${cat.id}"
                                               ${task.category_ids && task.category_ids.includes(cat.id) ? 'checked' : ''}>
                                        <span class="category-badge" style="background-color: ${cat.color || '#ccc'}">${cat.name}</span>
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
                <li class="completed-task-item" data-task-id="${task.id}" data-priority="${task.priority || 1}">
                    <div class="completed-task-content">
                        <span class="completed-task-text">${task.task_text}</span>
                    </div>
                    <div class="completed-task-meta">
                        ${task.completion_time ? `<span class="completed-time">Завершено: ${formatCompletionTime(task.completion_time)}</span>` : ''}
                        <span class="priority-indicator priority-${task.priority || 1}">
                            ${task.priority == 3 ? '❗ Высокий приоритет' :
                              task.priority == 2 ? '🔹 Средний приоритет' :
                              '🔸 Низкий приоритет'}
                        </span>
                        ${task.categories ? task.categories.split(',').map(cat_id => {
                            const cat = validCategories.find(c => c.id == parseInt(cat_id));
                            return cat ? `<span class="category-tag" style="background-color: ${cat.color || '#ccc'}">${cat.name}</span>` : '';
                        }).filter(tag => tag).join('') : ''}
                    </div>
                    <button type="button" class="restore-btn" data-task-id="${task.id}">Восстановить</button>
                </li>
            `).join('')}
        </ul>
    `;
}