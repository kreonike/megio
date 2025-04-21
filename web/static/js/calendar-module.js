import { updateTasksSection } from './tasks-module.js';
import { fetchCompletedTasks } from './completed-tasks.js';

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
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        if (!data.success || !data.data) throw new Error('Invalid response data');
        const tasksByDay = data.data.tasksByDay || {};

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
    console.log(`[updateTaskPriorityIndicator] Updating priority indicator, tasks: ${tasks.length}, completed: ${completedTasks.length}`);
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

export function bindDayClickHandlers(year, month, day) {
    console.log(`[bindDayClickHandlers] Binding handlers for ${year}-${month}-${day}`);
    const links = document.querySelectorAll('.day-link');
    if (!links.length) {
        console.error('[bindDayClickHandlers] No day links found in DOM');
    }
    links.forEach(link => {
        link.removeEventListener('click', handleDayClick);
        link.addEventListener('click', handleDayClick);
    });

    function handleDayClick(e) {
        e.preventDefault();
        console.log('[handleDayClick] Day link clicked');
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
        if (!tasksSection) {
            console.error('[handleDayClick] Tasks section not found in DOM');
            return;
        }
        tasksSection.innerHTML = '<p>Загрузка...</p>';

        Promise.all([
            fetch(`/tasks/${year}/${month}/${dayAttr}`, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            }).then(response => {
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            }).catch(error => {
                console.error('[handleDayClick] Error fetching tasks:', error);
                return { success: false, data: null };
            }),
            fetchCompletedTasks(year, month, dayAttr).catch(error => {
                console.error('[handleDayClick] Error fetching completed tasks:', error);
                return [];
            })
        ])
        .then(([taskData, completedTasks]) => {
            console.log('[handleDayClick] Task data received:', taskData, 'Completed tasks:', completedTasks);
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
                tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
            }
        })
        .catch(error => {
            console.error('[handleDayClick] Error loading tasks:', error);
            tasksSection.innerHTML = '<p>Ошибка загрузки задач: ' + error.message + '</p>';
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth() + 1;
    const day = today.getDate();
    console.log(`[DOMContentLoaded] Initializing for ${year}-${month}-${day}`);
    bindDayClickHandlers(year, month, day);
    updateCalendar(year, month);

    const tasksSection = document.querySelector('.tasks-section');
    if (!tasksSection) {
        console.error('[DOMContentLoaded] Tasks section not found in DOM');
        return;
    }
    tasksSection.innerHTML = '<p>Загрузка...</p>';

    Promise.all([
        fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        }).then(response => response.json()).catch(error => {
            console.error('[DOMContentLoaded] Error fetching tasks:', error);
            return { success: false, data: null };
        }),
        fetchCompletedTasks(year, month, day).catch(error => {
            console.error('[DOMContentLoaded] Error fetching completed tasks:', error);
            return [];
        })
    ])
    .then(([taskData, completedTasks]) => {
        if (taskData.success && taskData.data) {
            updateTasksSection(
                taskData.data.tasks || [],
                completedTasks || [],
                `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
                day,
                taskData.data.categories || []
            );
        } else {
            console.error('[DOMContentLoaded] Invalid task data:', taskData);
            tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
        }
    })
    .catch(error => {
        console.error('[DOMContentLoaded] Error loading initial tasks:', error);
        tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
    });
});