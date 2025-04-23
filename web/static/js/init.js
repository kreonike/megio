import { bindDayClickHandlers } from './event-handlers.js';
import { renderTasks } from './tasks-module.js';
import { initFilters } from './filters.js';

async function init() {
    console.log('[init] window.initialTasksData:', window.initialTasksData);
    console.log('[init] window.currentDate:', window.currentDate);

    const defaultDate = {
        year: new Date().getFullYear(),
        month: new Date().getMonth() + 1,
        day: new Date().getDate()
    };
    const defaultTasksData = {
        tasks: [],
        categories: [],
        completed_tasks: []
    };

    const tasksData = window.initialTasksData || defaultTasksData;
    const date = window.currentDate || defaultDate;

    console.log('[init] Rendering initial tasks for', date);
    renderTasks(
        tasksData.tasks,
        tasksData.categories,
        date.year,
        date.month,
        date.day,
        tasksData.completed_tasks
    );

    bindDayClickHandlers();
    initFilters();
}

init().catch(error => {
    console.error('[init] Initialization error:', error);
});