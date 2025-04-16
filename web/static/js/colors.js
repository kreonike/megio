// colors.js
export const COLORS = {
    WORK: '#87CEEB',       // Голубой для работы (ID 1)
    PERSONAL: '#FFA500',   // Оранжевый для личного (ID 2)
    COMPLETED: '#4CAF50',  // Зеленый для выполненных задач
    OVERDUE: '#F44336',    // Красный для просроченных
    WEEKEND: 'var(--weekend-bg-color)',
    DEFAULT: 'transparent'
};

export function getDayCellBackground(tasks, completedTasks, isWeekend) {
    const allTasks = [...(tasks || []), ...(completedTasks || [])];

    // 1. Проверка категорий (высший приоритет)
    const categoryIds = new Set();
    allTasks.forEach(task => {
        if (task.category_ids) {
            task.category_ids.forEach(id => categoryIds.add(id));
        }
    });

    // Категории (ID 1 - работа, ID 2 - личное)
    if (categoryIds.size === 1) {
        const categoryId = Array.from(categoryIds)[0];
        if (categoryId === 1) return COLORS.WORK;    // Работа - оранжевый
        if (categoryId === 2) return COLORS.PERSONAL; // Личное - голубой
    }

    // 2. Все задачи выполнены
    const allCompleted = allTasks.length > 0 && allTasks.every(task => task.completed);
    if (allCompleted) return COLORS.COMPLETED;

    // 3. Просроченные задачи
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const taskDate = new Date(allTasks[0]?.date || now);

    const hasOverdue = allTasks.some(task => !task.completed && taskDate < today);
    if (hasOverdue) return COLORS.OVERDUE;

    // 4. Выходные
    if (isWeekend) return COLORS.WEEKEND;

    return COLORS.DEFAULT;
}

export function applyDayCellStyles(dayCell, tasks, completedTasks, isWeekend) {
    // Сброс всех классов
    dayCell.classList.remove(
        'category-work',
        'category-personal',
        'all-tasks-completed',
        'has-overdue-tasks',
        'weekend',
        'has-tasks'
    );

    const color = getDayCellBackground(tasks, completedTasks, isWeekend);

    switch(color) {
        case COLORS.WORK:
            dayCell.classList.add('category-work');
            break;
        case COLORS.PERSONAL:
            dayCell.classList.add('category-personal');
            break;
        case COLORS.COMPLETED:
            dayCell.classList.add('all-tasks-completed');
            break;
        case COLORS.OVERDUE:
            dayCell.classList.add('has-overdue-tasks');
            break;
        case COLORS.WEEKEND:
            dayCell.classList.add('weekend');
            break;
    }

    // Индикатор невыполненных задач
    const hasIncompleteTasks = [...(tasks || [])].some(t => !t.completed);
    if (hasIncompleteTasks) {
        dayCell.classList.add('has-tasks');
    }
}