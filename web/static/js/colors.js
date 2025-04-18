// static/js/colors.js

export function applyDayCellStyles(dayCell, tasks = [], completedTasks = [], isWeekend = false) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const dayDate = new Date(
        parseInt(dayCell.dataset.year),
        parseInt(dayCell.dataset.month) - 1,
        parseInt(dayCell.dataset.day)
    );

    // Объединяем все задачи (активные и завершенные)
    const allTasks = [...tasks, ...completedTasks.map(task => ({
        ...task,
        completed: true,
        priority: task.priority || 1
    }))];

    // Проверяем состояния
    let hasOverdue = false;
    let allCompleted = allTasks.length > 0;
    let hasWorkCategory = false;
    let hasPersonalCategory = false;

    allTasks.forEach(task => {
        // Проверка просроченных задач
        if (dayDate < today && !task.completed) {
            hasOverdue = true;
        }

        // Проверка завершенности всех задач
        if (!task.completed) {
            allCompleted = false;
        }

        // Проверка категорий
        if (task.category_ids) {
            if (task.category_ids.includes(1)) hasWorkCategory = true;
            if (task.category_ids.includes(2)) hasPersonalCategory = true;
        } else if (task.categories) {
            if (task.categories.includes('Работа')) hasWorkCategory = true;
            if (task.categories.includes('Личное')) hasPersonalCategory = true;
        }
    });

    // Сбрасываем все классы стилей
    const styleClasses = [
        'has-overdue-tasks',
        'all-tasks-completed',
        'category-work',
        'category-personal',
        'has-tasks'
    ];
    styleClasses.forEach(cls => dayCell.classList.remove(cls));

    // Применяем соответствующие стили
    if (allCompleted && allTasks.length > 0) {
        dayCell.classList.add('all-tasks-completed');
    } else if (hasOverdue) {
        dayCell.classList.add('has-overdue-tasks');
    } else if (tasks.length > 0) {
        dayCell.classList.add('has-tasks');
    }

    if (hasWorkCategory) {
        dayCell.classList.add('category-work');
    }
    if (hasPersonalCategory) {
        dayCell.classList.add('category-personal');
    }

    // Обновляем индикатор количества задач
    updateTaskCounter(dayCell, tasks);
}

function updateTaskCounter(dayCell, tasks = []) {
    let badge = dayCell.querySelector('.task-count-badge');
    const activeTasks = tasks.filter(task => !task.completed);

    if (activeTasks.length > 0) {
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'task-count-badge';
            dayCell.querySelector('.day-link').appendChild(badge);
        }

        badge.textContent = activeTasks.length;
        badge.className = 'task-count-badge';

        // Определяем максимальный приоритет среди активных задач
        const maxPriority = Math.max(...activeTasks.map(task => task.priority || 1));
        if (maxPriority === 3) {
            badge.classList.add('priority-high');
        } else if (maxPriority === 2) {
            badge.classList.add('priority-medium');
        } else {
            badge.classList.add('priority-low');
        }
    } else if (badge) {
        badge.remove();
    }
}