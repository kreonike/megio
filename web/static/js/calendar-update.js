import {
    formatDateToRussian,
    formatDateForInput,
    bindTimeSpinnerEvents
} from "./time.js";

import { updateCompletedTasksSection, fetchCompletedTasks } from './completed-tasks.js';

export function updateTasksSection(tasks, date, day, categories) {
    console.log(`[updateTasksSection] Updating for date ${date}, day ${day}`);
    console.log(`[updateTasksSection] Received tasks:`, tasks);
    console.log(`[updateTasksSection] Received categories:`, categories);

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

                        <!-- Форма напоминания -->
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
                `;
            }).join('')}
        </ul>
    `;

    // Привязываем обработчики событий
    const yearNum = parseInt(year);
    const monthNum = parseInt(month);
    bindAllTaskHandlers(yearNum, monthNum, day);

    // Привязываем обработчики для спиннера времени
    document.querySelectorAll('.edit-time-input').forEach(input => {
        bindTimeSpinnerEvents(input);
    });

    // Привязываем обработчик для основного поля времени
    const taskTimeInput = document.getElementById('task-time');
    if (taskTimeInput) {
        bindTimeSpinnerEvents(taskTimeInput);
    }

    // Обработчик для чекбокса повторения в основной форме
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

    // Обработчики для чекбоксов повторения в формах редактирования
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

    // Обработчики фильтров
    document.getElementById('category-filter')?.addEventListener('change', applyFilters);
    document.getElementById('priority-filter')?.addEventListener('change', applyFilters);

    // Загружаем выполненные задачи
    fetchCompletedTasks(yearNum, monthNum, day);
}

function applyFilters() {
    const categoryFilter = document.getElementById('category-filter')?.value;
    const priorityFilter = document.getElementById('priority-filter')?.value;

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
        if (!data.success || !data.data) {
            console.error('[updateCalendar] Invalid response data:', data);
            throw new Error('Invalid response data');
        }
        const tasksByDay = data.data.tasksByDay || {};
        document.querySelectorAll('.day-link').forEach(link => {
            const day = link.getAttribute('data-day');
            const dayCell = link.closest('.day-cell');
            let badge = link.querySelector('.task-count-badge');

            if (day && tasksByDay.hasOwnProperty(day)) {
                const tasks = tasksByDay[day];
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
                } else {
                    if (badge) {
                        badge.remove();
                    }
                    dayCell.classList.remove('has-tasks');
                }
            }
        });
    })
    .catch(error => {
        console.error('[updateCalendar] Error updating calendar:', error);
        alert('Ошибка при обновлении календаря: ' + error.message);
        throw error;
    })
    .finally(() => {
        document.querySelectorAll('.task-count-badge').forEach(badge => {
            badge.classList.remove('updating');
        });
    });
}

export function updateTaskPriorityIndicator(dayElement, tasks) {
    const badge = dayElement.querySelector('.task-count-badge');
    if (!badge) return;
    if (!tasks || tasks.length === 0) {
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
}

export function bindAllTaskHandlers(year, month, day) {
    console.log(`[bindAllTaskHandlers] Binding handlers for ${year}-${month}-${day}`);

    // Очистить существующие обработчики
    const links = document.querySelectorAll('.day-link');
    links.forEach(link => {
        link.removeEventListener('click', handleDayClick);
    });

    // Привязать новые обработчики
    links.forEach(link => {
        console.log('[bindAllTaskHandlers] Binding click for day:', link.getAttribute('data-day'));
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

        // Показать индикатор загрузки
        const tasksSection = document.querySelector('.tasks-section');
        if (tasksSection) {
            tasksSection.innerHTML = '<p>Загрузка...</p>';
        }

        fetch(`/tasks/${year}/${month}/${dayAttr}`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => {
            if (!response.ok) {
                console.error('[handleDayClick] Fetch failed with status:', response.status);
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('[handleDayClick] Received data:', data);
            if (data.success && data.data) {
                updateTasksSection(data.data.tasks || [], date, dayAttr, data.data.categories || []);
                updateTaskPriorityIndicator(this.closest('.day-cell'), data.data.tasks || []);
            } else {
                console.error('[handleDayClick] Invalid response data:', data);
                alert('Ошибка: сервер вернул некорректные данные');
                if (tasksSection) {
                    tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
                }
            }
        })
        .catch(error => {
            console.error('[handleDayClick] Error loading tasks:', error);
            alert('Ошибка при загрузке задач: ' + error.message);
            if (tasksSection) {
                tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
            }
        });
    }

    // Обработчик кнопки "Напомнить"
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

    // Обработчик подтверждения напоминания
    document.querySelectorAll('.remind-confirm-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            const remindForm = this.closest('.remind-form');
            const selectedReminders = Array.from(
                remindForm.querySelectorAll('input[name="remind_times"]:checked')
            ).map(el => parseInt(el.value));

            if (selectedReminders.length === 0) {
                alert('Пожалуйста, выберите хотя бы одно время напоминания');
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
                    console.log('Напоминания успешно установлены');
                } else {
                    console.error('Ошибка установки напоминаний:', data.error);
                    alert('Ошибка при установке напоминаний: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Произошла ошибка при отправке запроса');
            });
        });
    });

    // Обработчик отмены напоминания
    document.querySelectorAll('.cancel-remind').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.remind-form').classList.remove('active');
        });
    });

    // Обработчик кнопки "Редактировать"
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

    // Обработчик отмены редактирования
    document.querySelectorAll('.cancel-edit').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.edit-form').classList.remove('active');
        });
    });

    // Обработчик кнопки "Удалить"
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
                    fetch(`/tasks/${year}/${month}/${day}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.data) {
                            updateTasksSection(data.data.tasks || [], `${year}-${month}-${day}`, day, data.data.categories || []);
                            updateCalendar(year, month);
                        }
                    });
                } else {
                    alert('Ошибка при удалении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ошибка при удалении задачи');
            });
        });
    });

    // Обработчик кнопки "Выполнено"
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
                    fetch(`/tasks/${year}/${month}/${day}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.data) {
                            updateTasksSection(data.data.tasks || [], `${year}-${month}-${day}`, day, data.data.categories || []);
                            updateCalendar(year, month);
                            fetchCompletedTasks(year, month, day);
                        }
                    });
                } else {
                    alert('Ошибка при выполнении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ошибка при выполнении задачи');
            });
        });
    });

    // Обработчик отправки формы добавления задачи
    document.querySelector('.task-form')?.addEventListener('submit', function(e) {
        e.preventDefault();

        fetch(this.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: new FormData(this)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.reset();
                fetch(`/tasks/${year}/${month}/${day}`, {
                    method: 'GET',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success && data.data) {
                        updateTasksSection(data.data.tasks || [], `${year}-${month}-${day}`, day, data.data.categories || []);
                        updateCalendar(year, month);
                    }
                });
            } else {
                alert('Ошибка при добавлении задачи: ' + (data.error || 'Неизвестная ошибка'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при добавлении задачи');
        });
    });

    // Обработчик отправки формы редактирования задачи
    document.querySelectorAll('.edit-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            fetch(this.action, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: new FormData(this)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.classList.remove('active');
                    fetch(`/tasks/${year}/${month}/${day}`, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.data) {
                            updateTasksSection(data.data.tasks || [], `${year}-${month}-${day}`, day, data.data.categories || []);
                            updateCalendar(year, month);
                        }
                    });
                } else {
                    alert('Ошибка при обновлении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ошибка при обновлении задачи');
            });
        });
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth() + 1;
    const day = today.getDate();
    console.log(`[DOMContentLoaded] Initializing for ${year}-${month}-${day}`);

    // Привязать обработчики и обновить календарь
    bindAllTaskHandlers(year, month, day);
    updateCalendar(year, month);

    // Загрузить задачи для текущего дня
    fetch(`/tasks/${year}/${month}/${day}`, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.data) {
            updateTasksSection(
                data.data.tasks || [],
                `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
                day,
                data.data.categories || []
            );
        } else {
            console.error('[DOMContentLoaded] Invalid initial tasks data:', data);
        }
    })
    .catch(error => console.error('[DOMContentLoaded] Error loading initial tasks:', error));
});