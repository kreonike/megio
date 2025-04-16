// colors.js
export const COLORS = {
    WORK: '#FFA500',       // Оранжевый для работы
    PERSONAL: '#87CEEB',   // Голубой для личного
    COMPLETED: '#4CAF50',  // Зеленый для выполненных задач
    OVERDUE: '#F44336',    // Красный для просроченных
    DEFAULT: 'transparent' // Прозрачный (без категории)
};

export function getDayCellBackground(tasks, completedTasks, categories) {
    const allTasks = [...(tasks || []), ...(completedTasks || [])];

    if (allTasks.length === 0) return COLORS.DEFAULT;

    // Проверка на просроченные задачи
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const taskDate = new Date(allTasks[0].date || now); // предполагаем, что все задачи одного дня

    const hasOverdue = allTasks.some(task =>
        !task.completed && taskDate < today
    );

    if (hasOverdue) return COLORS.OVERDUE;

    // Проверка на все выполненные задачи
    const allCompleted = allTasks.every(task => task.completed);
    if (allCompleted) return COLORS.COMPLETED;

    // Проверка категорий
    const categoryIds = new Set();
    allTasks.forEach(task => {
        if (task.category_ids) {
            task.category_ids.forEach(id => categoryIds.add(id));
        }
    });

    const hasWork = categoryIds.has(1); // предполагаем, что 1 - это работа
    const hasPersonal = categoryIds.has(2); // предполагаем, что 2 - это личное

    if (hasWork && !hasPersonal) return COLORS.WORK;
    if (hasPersonal && !hasWork) return COLORS.PERSONAL;

    // Если несколько категорий или нет категорий
    return COLORS.DEFAULT;
}

export function applyDayCellStyles(dayCell, tasks, completedTasks, categories) {
    const color = getDayCellBackground(tasks, completedTasks, categories);

    // Сброс всех классов
    dayCell.classList.remove(
        'category-work',
        'category-personal',
        'all-tasks-completed',
        'has-overdue-tasks'
    );

    // Применение стилей в зависимости от цвета
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
        default:
            // Ничего не делаем для DEFAULT
            break;
    }
}