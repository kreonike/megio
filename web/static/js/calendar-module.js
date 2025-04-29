import { fetchMonthTasks, fetchCompletedTasks } from './api.js';

export function updateCalendar(year, month) {
    /**
     * Обновляет календарь для указанного года и месяца, отображая задачи.
     *
     * @param {number} year - Год календаря.
     * @param {number} month - Месяц календаря.
     */
    console.log(`[calendar-module/updateCalendar] Обновление для ${year}-${month}`);
    const badges = document.querySelectorAll('.task-count-badge');
    badges.forEach(badge => badge.classList.add('updating'));

    const calendarTable = document.querySelector('.calendar-table-container');
    calendarTable.classList.add('loading');

    // Запрашиваем активные и завершенные задачи для месяца
    return Promise.all([
        fetchMonthTasks(year, month),
        fetchMonthCompletedTasks(year, month)
    ])
        .then(([monthData, completedData]) => {
            if (!monthData.success || !monthData.data) throw new Error('Некорректные данные ответа для задач');
            const tasksByDay = monthData.data.tasksByDay || {};
            const completedTasksByDay = completedData || {};

            console.log('[calendar-module/updateCalendar] tasksByDay:', tasksByDay);
            console.log('[calendar-module/updateCalendar] completedTasksByDay:', completedTasksByDay);

            document.querySelectorAll('.day-link').forEach(link => {
                const day = link.getAttribute('data-day');
                const dayCell = link.closest('.day-cell');
                let badge = link.querySelector('.task-count-badge');

                if (day) {
                    const tasks = tasksByDay[day] || [];
                    const completedTasks = completedTasksByDay[day] || [];

                    dayCell.classList.remove('has-overdue-tasks', 'all-tasks-completed', 'has-tasks');
                    dayCell.style.background = '';

                    // Проверяем, есть ли активные задачи или только завершенные
                    if (tasks.length === 0 && completedTasks.length > 0) {
                        // Только завершенные задачи — применяем синий цвет
                        dayCell.classList.add('all-tasks-completed');
                        if (badge) badge.remove();
                    } else if (tasks.length > 0) {
                        const now = new Date();
                        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                        const taskDate = new Date(year, month - 1, day);

                        let hasOverdue = false;
                        let maxPriority = 1;
                        let colors = new Set();

                        tasks.forEach(task => {
                            if (taskDate < today && !task.completed) hasOverdue = true;
                            maxPriority = Math.max(maxPriority, task.priority || 1);
                            if (task.category_colors) {
                                task.category_colors.forEach(color => {
                                    if (/^#[0-9A-F]{6}$/i.test(color)) colors.add(color);
                                });
                            }
                        });

                        dayCell.classList.add('has-tasks');
                        if (hasOverdue) {
                            dayCell.classList.add('has-overdue-tasks');
                        }

                        const validColors = [...colors];
                        if (validColors.length === 1) {
                            dayCell.style.backgroundColor = `${validColors[0]}20`;
                        } else if (validColors.length > 1) {
                            const gradient = validColors.map(color => `${color} 0%, ${color} 50%`).join(',');
                            dayCell.style.background = `linear-gradient(135deg, ${gradient})`;
                        }

                        if (!badge) {
                            badge = document.createElement('span');
                            badge.className = 'task-count-badge';
                            link.appendChild(badge);
                        }

                        badge.textContent = tasks.length;
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
                        dayCell.classList.remove('has-tasks');
                    }
                }
            });
        })
        .catch(error => {
            console.error('[calendar-module/updateCalendar] Ошибка:', error);
            alert('Ошибка при обновлении календаря: ' + error.message);
            throw error;
        })
        .finally(() => {
            badges.forEach(badge => badge.classList.remove('updating'));
            calendarTable.classList.remove('loading');
        });
}

// Новая функция для получения завершенных задач за месяц
async function fetchMonthCompletedTasks(year, month) {
    console.log(`[calendar-module/fetchMonthCompletedTasks] Запрос завершённых задач для ${year}-${month}`);
    const daysInMonth = new Date(year, month, 0).getDate();
    const completedTasksByDay = {};

    // Запрашиваем завершенные задачи для каждого дня
    const promises = [];
    for (let day = 1; day <= daysInMonth; day++) {
        promises.push(
            fetchCompletedTasks(year, month, day)
                .then(data => ({ day, tasks: data.data?.completedTasks || [] }))
        );
    }

    const results = await Promise.all(promises);
    results.forEach(({ day, tasks }) => {
        if (tasks.length > 0) {
            completedTasksByDay[day] = tasks;
        }
    });

    return completedTasksByDay;
}

export function updateTaskPriorityIndicator(dayElement, tasks, completedTasks) {
    /**
     * Обновляет индикатор приоритета для дня в календаре.
     *
     * @param {HTMLElement} dayElement - Элемент дня в календаре.
     * @param {Array} tasks - Список задач.
     * @param {Array} completedTasks - Список завершённых задач.
     */
    console.log(`[calendar-module/updateTaskPriorityIndicator] Обновление индикатора приоритета, задачи: ${tasks.length}, завершённые: ${completedTasks.length}`);
    const badge = dayElement.querySelector('.task-count-badge');

    dayElement.classList.remove('has-tasks', 'has-overdue-tasks');

    if (tasks.length > 0) {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const day = parseInt(dayElement.querySelector('.day-link').getAttribute('data-day'));
        const taskDate = new Date(dayElement.closest('.calendar-table').dataset.year, dayElement.closest('.calendar-table').dataset.month - 1, day);

        let hasOverdue = taskDate < today && tasks.some(task => !task.completed);

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
                maxPriority = Math.max(maxPriority, task.priority || 1);
            });

            updatedBadge.textContent = tasks.length;
            updatedBadge.classList.remove('priority-low', 'priority-medium', 'priority-high');
            if (maxPriority === 3) updatedBadge.classList.add('priority-high');
            else if (maxPriority === 2) updatedBadge.classList.add('priority-medium');
            else updatedBadge.classList.add('priority-low');

            dayElement.classList.add('has-tasks');
            if (hasOverdue) {
                dayElement.classList.add('has-overdue-tasks');
            }
        }
    } else {
        if (badge) badge.remove();
    }
}