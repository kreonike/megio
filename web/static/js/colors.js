// colors.js
export const COLORS = {
    WORK: '#FFA500',       // Оранжевый для работы
    PERSONAL: '#87CEEB',   // Голубой для личного
    COMPLETED: '#4CAF50',  // Зеленый для выполненных задач
    OVERDUE: '#F44336',    // Красный для просроченных
    DEFAULT: 'transparent' // Без цвета
};

export function getDayCellBackground(tasks, completedTasks) {
    const allTasks = [...(tasks || []), ...(completedTasks || [])];

    if (allTasks.length === 0) return COLORS.DEFAULT;

    // Проверка на просроченные задачи
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const taskDate = new Date(allTasks[0].date || now);

    const hasOverdue = allTasks.some(task =>
        !task.completed && taskDate < today
    );

    if (hasOverdue) return COLORS.OVERDUE;

    // Проверка на все выполненные задачи
    const allCompleted = allTasks.every(task => task.completed);
    if (allCompleted) return COLORS.COMPLETED;

    // Проверка категорий (только если ровно одна категория)
    const categoryIds = new Set();
    allTasks.forEach(task => {
        if (task.category_ids) {
            task.category_ids.forEach(id => categoryIds.add(id));
        }
    });

    if (categoryIds.size === 1) {
        const categoryId = Array.from(categoryIds)[0];
        if (categoryId === 1) return COLORS.WORK;    // Работа
        if (categoryId === 2) return COLORS.PERSONAL; // Личное
    }

    // Во всех остальных случаях - без цвета
    return COLORS.DEFAULT;
}

export function applyDayCellStyles(dayCell, tasks, completedTasks) {
    const color = getDayCellBackground(tasks, completedTasks);

    // Сброс всех цветовых классов
    dayCell.classList.remove(
        'category-work',
        'category-personal',
        'all-tasks-completed',
        'has-overdue-tasks'
    );

    // Применяем только конкретные цветовые классы
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
        // Для COLORS.DEFAULT ничего не делаем - останется без цвета
    }
}