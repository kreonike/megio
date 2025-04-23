// static/js/calendar-module.js
import { fetchMonthTasks, fetchCompletedTasks } from './api.js';

export function updateCalendar(year, month) {
    console.log(`[calendar-module/updateCalendar] Updating for ${year}-${month}`);
    document.querySelectorAll('.task-count-badge').forEach(badge => {
        badge.classList.add('updating');
    });

    return fetchMonthTasks(year, month)
        .then(data => {
            if (!data.success || !data.data) throw new Error('Invalid response data');
            const tasksByDay = data.data.tasksByDay || {};

            const promises = [];
            for (let day = 1; day <= 31; day++) {
                promises.push(
                    fetchCompletedTasks(year, month, day)
                        .then(completedTasks => ({ day, completedTasks: completedTasks || [] }))
                        .catch(err => {
                            console.error(`[calendar-module/updateCalendar] Error fetching completed tasks for day ${day}:`, err);
                            return { day, completedTasks: [] };
                        })
                );
            }

            return Promise.all(promises).then(completedResults => {
                const completedTasksByDay = {};
                completedResults.forEach(result => {
                    completedTasksByDay[result.day] = result.completedTasks;
                });

                document.querySelectorAll('.day-link').forEach(link => {
                    const day = link.getAttribute('data-day');
                    const dayCell = link.closest('.day-cell');
                    let badge = link.querySelector('.task-count-badge');

                    if (day) {
                        const tasks = tasksByDay[day] || [];
                        const completedTasks = completedTasksByDay[day] || [];

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

                            allTasks.forEach(task => {
                                if (taskDate < today && !task.completed) hasOverdue = true;
                                if (!task.completed) allCompleted = false;
                                maxPriority = Math.max(maxPriority, task.priority || 1);
                            });

                            dayCell.classList.add('has-tasks');
                            if (hasOverdue) {
                                dayCell.classList.add('has-overdue-tasks');
                            } else if (allCompleted && allTasks.length > 0) {
                                dayCell.classList.add('all-tasks-completed');
                            }

                            if (!badge) {
                                badge = document.createElement('span');
                                badge.className = 'task-count-badge';
                                link.appendChild(badge);
                            }

                            badge.textContent = allTasks.length;
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
            });
        })
        .catch(error => {
            console.error('[calendar-module/updateCalendar] Error:', error);
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
    console.log(`[calendar-module/updateTaskPriorityIndicator] Updating priority indicator, tasks: ${tasks.length}, completed: ${completedTasks.length}`);
    const badge = dayElement.querySelector('.task-count-badge');
    const allTasks = [...(tasks || []), ...(completedTasks || []).map(task => ({
        ...task,
        priority: task.priority || 1
    }))];

    if (allTasks.length === 0) {
        dayElement.classList.remove('has-tasks', 'has-overdue-tasks', 'all-tasks-completed');
        if (badge) badge.remove();
        return;
    }

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
        allTasks.forEach(task => {
            maxPriority = Math.max(maxPriority, task.priority || 1);
        });

        updatedBadge.textContent = allTasks.length;
        updatedBadge.classList.remove('priority-low', 'priority-medium', 'priority-high');
        if (maxPriority === 3) updatedBadge.classList.add('priority-high');
        else if (maxPriority === 2) updatedBadge.classList.add('priority-medium');
        else updatedBadge.classList.add('priority-low');
    }
}