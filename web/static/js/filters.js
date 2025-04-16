// filters.js
import { updateCalendar, updateTasksSection, year, month } from "./calendar-update.js";
import { fetchCompletedTasks } from './completed-tasks.js';
import { applyDayCellStyles } from "./colors.js";

// Функция применения фильтров
export function applyFilters() {
    const categoryFilter = document.getElementById('category-filter')?.value || '';
    const priorityFilter = document.getElementById('priority-filter')?.value || '';

    // Получаем список всех категорий из DOM
    const categoryOptions = document.querySelectorAll('#category-filter option');
    const categories = Array.from(categoryOptions)
        .filter(opt => opt.value)
        .map(opt => ({
            id: parseInt(opt.value),
            name: opt.textContent,
            color: getComputedStyle(document.querySelector(`.category-badge[data-category-id="${opt.value}"]`)).backgroundColor
        }));

    // Фильтрация задач в боковой панели
    document.querySelectorAll('.task-item, .completed-task-item').forEach(item => {
        const itemCategories = item.dataset.categories ? item.dataset.categories.split(',').map(id => parseInt(id)) : [];
        const itemPriority = item.dataset.priority;
        const categoryMatch = !categoryFilter || itemCategories.includes(parseInt(categoryFilter));
        const priorityMatch = !priorityFilter || itemPriority === priorityFilter;
        item.style.display = (categoryMatch && priorityMatch) ? '' : 'none';
    });

    // Обновляем все ячейки календаря на основе фильтра
    document.querySelectorAll('.day-cell').forEach(dayCell => {
        const day = dayCell.querySelector('.day-link')?.getAttribute('data-day');
        if (day && year && month && window.tasksCache[`${year}-${month}-${day}`]) {
            const cachedData = window.tasksCache[`${year}-${month}-${day}`];
            let tasks = cachedData.tasks || [];
            let completedTasks = cachedData.completedTasks || [];

            // Фильтруем задачи по выбранным фильтрам
            tasks = tasks.filter(task =>
                (!categoryFilter || (task.category_ids && task.category_ids.includes(parseInt(categoryFilter)))) &&
                (!priorityFilter || task.priority == priorityFilter)
            );

            completedTasks = completedTasks.filter(task =>
                (!categoryFilter || (task.category_ids && task.category_ids.includes(parseInt(categoryFilter)))) &&
                (!priorityFilter || task.priority == priorityFilter)
            );

            // Применяем стили к ячейке
            applyDayCellStyles(dayCell, tasks, completedTasks, categories);
            updateTaskPriorityIndicator(dayCell, tasks, completedTasks);
        }
    });
}

// Функция обновления индикатора приоритета задач
export function updateTaskPriorityIndicator(dayElement, tasks, completedTasks) {
    if (!year || !month) {
        const today = new Date();
        year = today.getFullYear();
        month = today.getMonth() + 1;
    }

    const badge = dayElement.querySelector('.task-count-badge');
    const allTasks = [...(tasks || []), ...(completedTasks || []).map(task => ({
        ...task,
        priority: task.priority || 1,
        completed: 1
    }))];

    dayElement.classList.remove('has-tasks');

    if (allTasks.length === 0) {
        if (badge) badge.remove();
        return;
    }

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const day = parseInt(dayElement.querySelector('.day-link')?.getAttribute('data-day'));
    const taskDate = new Date(year, month - 1, day);

    // Подсчет задач для бейджа
    const incompleteTasks = tasks.filter(task => !task.completed);

    if (incompleteTasks.length > 0) {
        dayElement.classList.add('has-tasks');

        if (!badge) {
            const link = dayElement.querySelector('.day-link');
            if (link) {
                const newBadge = document.createElement('span');
                newBadge.className = 'task-count-badge';
                link.appendChild(newBadge);
            }
        }

        if (badge) {
            badge.textContent = incompleteTasks.length;
            badge.classList.remove('priority-low', 'priority-medium', 'priority-high');

            const maxPriority = Math.max(...incompleteTasks.map(task => task.priority || 1));
            if (maxPriority === 3) {
                badge.classList.add('priority-high');
            } else if (maxPriority === 2) {
                badge.classList.add('priority-medium');
            } else {
                badge.classList.add('priority-low');
            }
        }
    } else {
        if (badge) badge.remove();
    }
}

// Инициализация обработчиков фильтров
export function initFilters() {
    const categoryFilter = document.getElementById('category-filter');
    const priorityFilter = document.getElementById('priority-filter');

    if (categoryFilter) {
        categoryFilter.removeEventListener('change', applyFilters);
        categoryFilter.addEventListener('change', applyFilters);
    }

    if (priorityFilter) {
        priorityFilter.removeEventListener('change', applyFilters);
        priorityFilter.addEventListener('change', applyFilters);
    }

    // Применяем фильтры при загрузке
    setTimeout(applyFilters, 100);
}