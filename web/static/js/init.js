document.addEventListener('DOMContentLoaded', async () => {
    console.log('[init] DOMContentLoaded fired');
    const tasksSection = document.querySelector('.tasks-section');
    if (!tasksSection) {
        console.error('[init] Tasks section not found');
        return;
    }

    // Получаем year и month из currentDate или из атрибутов calendar-table
    let year, month, day;
    if (window.currentDate && window.currentDate.year && window.currentDate.month) {
        year = window.currentDate.year;
        month = window.currentDate.month;
        day = window.currentDate.day;
        console.log('[init] currentDate:', window.currentDate);
    } else {
        console.warn('[init] currentDate не определён, используем данные из calendar-table');
        const calendarTable = document.querySelector('.calendar-table');
        if (calendarTable) {
            year = parseInt(calendarTable.dataset.year, 10);
            month = parseInt(calendarTable.dataset.month, 10);
            day = new Date().getDate();
            console.log('[init] Получены данные из calendar-table:', { year, month, day });
        } else {
            console.error('[init] Не удалось определить year и month, используем текущую дату');
            const today = new Date();
            year = today.getFullYear();
            month = today.getMonth() + 1;
            day = today.getDate();
        }
    }

    console.log(`[init] Initializing for ${year}-${month}-${day}`);

    try {
        // Динамические импорты для избежания ошибок загрузки модулей
        const { updateCalendar } = await import('./calendar-module.js');
        const { fetchTasks, fetchCompletedTasks } = await import('./api.js');
        const { updateTasksSection } = await import('./tasks-module.js');
        const { bindDayClickHandlers, bindTaskEventHandlers } = await import('./event-handlers.js');

        // Инициализация календаря
        console.log('[init] Вызов updateCalendar:', { year, month });
        await updateCalendar(year, month);
        console.log('[init] Calendar initialized');

        // Загрузка задач и завершённых задач
        console.log('[init] Загрузка задач для:', { year, month, day });
        const [taskData, completedTasks] = await Promise.all([
            fetchTasks(year, month, day),
            fetchCompletedTasks(year, month, day)
        ]);

        if (taskData.success && taskData.data) {
            console.log('[init] Task data received:', taskData.data);
            // Передаем категории из taskData.data.categories
            updateTasksSection(
                taskData.data.tasks || [],
                completedTasks?.data?.completedTasks || [],
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
        console.log('[init] Привязка обработчиков кликов по дням');
        bindDayClickHandlers(year, month);

        // Выделение текущего дня (только если это текущий месяц и год)
        const today = new Date();
        const isCurrentMonth = year === today.getFullYear() && month === today.getMonth() + 1;
        if (isCurrentMonth) {
            const todayLink = document.querySelector(`.day-link[data-day="${day}"]`);
            if (todayLink) {
                console.log('[init] Выделение текущего дня:', day);
                todayLink.classList.add('selected');
            }
        }

        // Обработчик для навигационных ссылок по месяцам
        document.querySelectorAll('.month-nav-btn').forEach(link => {
            link.addEventListener('click', async (e) => {
                e.preventDefault();
                console.log('[init] Month navigation clicked:', link.href);
                const href = link.getAttribute('href');
                window.location.href = href; // Переход по ссылке
                const url = new URL(href, window.location.origin);
                const newYear = parseInt(url.pathname.split('/')[2], 10);
                const newMonth = parseInt(url.pathname.split('/')[3], 10);
                console.log('[init] Navigating to:', { newYear, newMonth });
                await import('./calendar-module.js').then(({ updateCalendar }) => {
                    updateCalendar(newYear, newMonth);
                });
            });
        });
    } catch (error) {
        console.error('[init] Error:', error);
        tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
        tasksSection.classList.add('loaded');
    }
});