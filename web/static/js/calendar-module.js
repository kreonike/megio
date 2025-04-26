// static/js/calendar-module.js
import { fetchMonthTasks } from './api.js';

export function updateCalendar(year, month) {
    /**
     * Обновляет календарь для указанного года и месяца, отображая задачи.
     *
     * @param {number} year - Год календаря.
     * @param {number} month - Месяц календаря.
     */
    console.log(`[calendar-module/updateCalendar] Обновление для ${year}-${month}`);
    document.querySelectorAll('.task-count-badge').forEach(badge => {
        badge.classList.add('updating');
    });

    return fetchMonthTasks(year, month)
        .then(data => {
            if (!data.success || !data.data) throw new Error('Некорректные данные ответа');
            const tasksByDay = data.data.tasksByDay || {};

            document.querySelectorAll('.day-link').forEach(link => {
                const day = link.getAttribute('data-day');
                const dayCell = link.closest('.day-cell');
                let badge = link.querySelector('.task-count-badge');

                if (day) {
                    const tasks = tasksByDay[day] || [];
                    dayCell.classList.remove('has-overdue-tasks', 'all-tasks-completed', 'has-tasks');

                    dayCell.style.background = '';

                    if (tasks.length > 0) {
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
                                task.category_colors.forEach(color => colors.add(color));
                            }
                        });

                        dayCell.classList.add('has-tasks');
                        if (hasOverdue) {
                            dayCell.classList.add('has-overdue-tasks');
                        }

                        if (colors.size === 1) {
                            dayCell.style.backgroundColor = `${[...colors][0]}20`;
                        } else if (colors.size > 1) {
                            const gradient = [...colors].map(color => `${color} 0%, ${color} 50%`).join(',');
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
            document.querySelectorAll('.task-count-badge').forEach(badge => {
                badge.classList.remove('updating');
            });
        });
}

export function updateTaskPriorityIndicator(dayElement, tasks, completedTasks) {
    /**
     * Обновляет индикатор приоритета для дня в календаре.

     * @param {HTMLElement} dayElement - Элемент дня в календаре.
     * @param {Array} tasks - Список задач.
     * @param {Array} completedTasks - Список завершённых задач.
     */
    console.log(`[calendar-module/updateTaskPriorityIndicator] Обновление индикатора приоритета, задачи: ${tasks.length}, завершённые: ${completedTasks.length}`);
    const badge = dayElement.querySelector('.task-count-badge');

    dayElement.classList.remove('has-tasks', 'all-tasks-completed');

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

            if (!hasOverdue) {
                dayElement.classList.add('has-tasks');
            } else {
                dayElement.classList.add('has-overdue-tasks');
            }
        }
    } else if (completedTasks.length > 0) {
        if (badge) badge.remove();
        dayElement.classList.add('all-tasks-completed');
    } else {
        if (badge) badge.remove();
    }
}