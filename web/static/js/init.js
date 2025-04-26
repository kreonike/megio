document.addEventListener('DOMContentLoaded', async () => {
    console.log('[init] DOMContentLoaded fired');
    const tasksSection = document.querySelector('.tasks-section');
    if (!tasksSection) {
        console.error('[init] Tasks section not found');
        return;
    }

    try {
        // Динамические импорты для избежания ошибок загрузки модулей
        const { updateCalendar } = await import('./calendar-module.js');
        const { fetchTasks, fetchCompletedTasks } = await import('./api.js');
        const { updateTasksSection } = await import('./tasks-module.js');
        const { bindDayClickHandlers, bindTaskEventHandlers } = await import('./event-handlers.js');

        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth() + 1;
        const day = today.getDate();
        console.log(`[init] Initializing for ${year}-${month}-${day}`);

        // Инициализация календаря
        await updateCalendar(year, month);
        console.log('[init] Calendar initialized');

        // Загрузка задач и завершенных задач
        const [taskData, completedTasks] = await Promise.all([
            fetchTasks(year, month, day),
            fetchCompletedTasks(year, month, day)
        ]);

        if (taskData.success && taskData.data) {
            console.log('[init] Task data received:', taskData.data);
            // Передаем категории из taskData.data.categories
            updateTasksSection(
                taskData.data.tasks || [],
                completedTasks || [],
                `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
                day,
                taskData.data.categories || []
            );
            tasksSection.classList.add('loaded');

            // Привязываем обработчики для основной формы
            bindTaskEventHandlers(year, month, day);
        } else {
            console.error('[init] Invalid task data:', taskData);
            tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
            tasksSection.classList.add('loaded');
        }

        // Привязка обработчиков
        bindDayClickHandlers(year, month);

        // Выделение текущего дня
        const todayLink = document.querySelector(`.day-link[data-day="${day}"]`);
        if (todayLink) {
            todayLink.classList.add('selected');
        }
    } catch (error) {
        console.error('[init] Error:', error);
        tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
        tasksSection.classList.add('loaded');
    }
});