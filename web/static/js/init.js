import { updateCalendar } from './calendar-module.js';
import { fetchTasks, fetchCompletedTasks } from './api.js';
import { updateTasksSection } from './tasks-module.js';
import { bindDayClickHandlers } from './event-handlers.js';

console.log('[init] Starting initialization');
console.log('[init] Loaded scripts:', Array.from(document.scripts).map(s => s.src));

document.addEventListener('DOMContentLoaded', async () => {
    console.log('[init] DOMContentLoaded fired');
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth() + 1;
    const day = today.getDate();
    console.log(`[init] Initializing for ${year}-${month}-${day}`);

    // Инициализация календаря
    try {
        await updateCalendar(year, month);
        console.log('[init] Calendar initialized');
    } catch (err) {
        console.error('[init] Error initializing calendar:', err);
    }

    // Загрузка задач для текущего дня
    const tasksSection = document.querySelector('.tasks-section');
    if (!tasksSection) {
        console.error('[init] Tasks section not found in DOM');
        return;
    }
    tasksSection.innerHTML = '<p>Загрузка...</p>';

    try {
        const [taskData, completedTasks] = await Promise.all([
            fetchTasks(year, month, day),
            fetchCompletedTasks(year, month, day)
        ]);
        if (taskData.success && taskData.data) {
            updateTasksSection(
                taskData.data.tasks || [],
                completedTasks || [],
                `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
                day,
                [] // Категории уже в DOM
            );
        } else {
            console.error('[init] Invalid task data:', taskData);
            tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
        }
    } catch (error) {
        console.error('[init] Error loading initial tasks:', error);
        tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
    }

    // Привязка обработчиков кликов по дням
    bindDayClickHandlers(year, month);

    // Выделение текущего дня
    const todayLink = document.querySelector(`.day-link[data-day="${day}"]`);
    if (todayLink) {
        todayLink.classList.add('selected');
    }
});