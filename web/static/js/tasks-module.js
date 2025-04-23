import { fetchTasks, addTask, completeTask, fetchCompletedTasks } from './api.js';
import { renderTasks, updateTasksSection } from './tasks-module.js';
import { showNotification } from './utils.js';
import { updateCalendar } from './calendar-module.js';

export function bindDayClickHandlers() {
    document.addEventListener('DOMContentLoaded', () => {
        const days = document.querySelectorAll('.calendar-day');
        console.log('[event-handlers/bindDayClickHandlers] Found days:', days.length);
        days.forEach(day => {
            day.addEventListener('click', () => handleDayClick(day));
        });
    });
}

async function handleDayClick(dayElement) {
    const year = dayElement.dataset.year;
    const month = dayElement.dataset.month;
    const day = dayElement.dataset.day;

    console.log('[event-handlers/handleDayClick] Clicked day:', { year, month, day });

    if (!year || !month || !day) {
        console.error(`[event-handlers/handleDayClick] Invalid data: year=${year}, month=${month}, day=${day}`);
        showNotification('Ошибка: не удалось определить дату', 'error');
        return;
    }

    console.log(`[event-handlers/handleDayClick] Loading tasks for ${year}-${month}-${day}`);
    try {
        const [tasksResponse, completedTasksResponse] = await Promise.all([
            fetchTasks(year, month, day),
            fetchCompletedTasks(year, month, day)
        ]);
        console.log('[event-handlers/handleDayClick] Tasks response:', tasksResponse);
        console.log('[event-handlers/handleDayClick] Completed tasks response:', completedTasksResponse);
        renderTasks(
            tasksResponse.data.tasks,
            tasksResponse.data.categories,
            year,
            month,
            day,
            completedTasksResponse.data.completed_tasks
        );
        bindTaskEventHandlers(year, month, day); // Привязываем обработчики для формы
    } catch (error) {
        console.error(`[event-handlers/handleDayClick] Error for ${year}-${month}-${day}:`, error);
        showNotification('Ошибка при загрузке задач', 'error');
    }
}

export function bindTaskEventHandlers(year, month, day) {
    if (!year || !month || !day) {
        console.error(`[event-handlers/bindTaskEventHandlers] Invalid parameters: year=${year}, month=${month}, day=${day}`);
        return;
    }

    const form = document.querySelector('#task-form');
    console.log('[event-handlers/bindTaskEventHandlers] Task form found:', !!form);
    form?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const taskData = {
            task: formData.get('task'),
            time: formData.get('time') || null,
            priority: parseInt(formData.get('priority') || '1'),
            categories: formData.getAll('categories').map(Number),
            repeat_enabled: formData.get('repeat_enabled') === 'on',
            repeat_days: parseInt(formData.get('repeat_days') || '0'),
            repeat_start: formData.get('repeat_start') || null,
            repeat_end: formData.get('repeat_end') || null
        };
        try {
            await addTask(year, month, day, taskData);
            const [tasksResponse, completedTasksResponse] = await Promise.all([
                fetchTasks(year, month, day),
                fetchCompletedTasks(year, month, day)
            ]);
            updateTasksSection(
                tasksResponse.data.tasks,
                completedTasksResponse.data.completed_tasks,
                tasksResponse.data.categories
            );
            updateCalendar(year, month); // Обновляем календарь
            showNotification('Задача добавлена', 'success');
            form.reset();
        } catch (error) {
            console.error('[event-handlers/addTask] Error:', error);
            showNotification('Ошибка при добавлении задачи', 'error');
        }
    });

    document.querySelectorAll('.complete-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const taskId = btn.dataset.taskId;
            console.log(`[event-handlers/completeBtn] Completing task ${taskId} for ${year}-${month}-${day}`);
            try {
                await completeTask(taskId, year, month, day);
                const [tasksResponse, completedTasksResponse] = await Promise.all([
                    fetchTasks(year, month, day),
                    fetchCompletedTasks(year, month, day)
                ]);
                updateTasksSection(
                    tasksResponse.data.tasks,
                    completedTasksResponse.data.completed_tasks,
                    tasksResponse.data.categories
                );
                updateCalendar(year, month); // Обновляем календарь
                showNotification('Задача завершена', 'success');
            } catch (error) {
                console.error('[event-handlers/completeBtn] Error:', error);
                showNotification('Ошибка при завершении задачи', 'error');
            }
        });
    });
}