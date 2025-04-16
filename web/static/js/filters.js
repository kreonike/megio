// filters.js
import { updateCalendar, updateTasksSection, year, month } from "./calendar-update.js";
import { fetchCompletedTasks } from './completed-tasks.js';
import { applyDayCellStyles } from "./colors.js";

export function applyFilters() {
    const categoryFilter = document.getElementById('category-filter')?.value || '';
    const priorityFilter = document.getElementById('priority-filter')?.value || '';

    // Фильтрация задач в боковой панели
    document.querySelectorAll('.task-item, .completed-task-item').forEach(item => {
        const itemCategories = item.dataset.categories ?
            item.dataset.categories.split(',').map(id => parseInt(id)) : [];
        const itemPriority = item.dataset.priority;

        const categoryMatch = !categoryFilter || itemCategories.includes(parseInt(categoryFilter));
        const priorityMatch = !priorityFilter || itemPriority === priorityFilter;

        item.style.display = (categoryMatch && priorityMatch) ? '' : 'none';
    });

    // Обновление ячеек календаря
    document.querySelectorAll('.day-cell').forEach(dayCell => {
        const day = dayCell.querySelector('.day-link')?.getAttribute('data-day');
        if (day && year && month && window.tasksCache[`${year}-${month}-${day}`]) {
            const cachedData = window.tasksCache[`${year}-${month}-${day}`];
            let tasks = cachedData.tasks || [];
            let completedTasks = cachedData.completedTasks || [];

            // Фильтрация задач
            tasks = tasks.filter(task =>
                (!categoryFilter || (task.category_ids && task.category_ids.includes(parseInt(categoryFilter)))) &&
                (!priorityFilter || task.priority == priorityFilter)
            );

            completedTasks = completedTasks.filter(task =>
                (!categoryFilter || (task.category_ids && task.category_ids.includes(parseInt(categoryFilter)))) &&
                (!priorityFilter || task.priority == priorityFilter)
            );

            // Применение стилей
            applyDayCellStyles(dayCell, tasks, completedTasks);
            updateTaskPriorityIndicator(dayCell, tasks, completedTasks);
        }
    });
}

export function updateTaskPriorityIndicator(dayElement, tasks = [], completedTasks = []) {
    if (!year || !month) {
        const today = new Date();
        year = today.getFullYear();
        month = today.getMonth() + 1;
    }

    const badge = dayElement.querySelector('.task-count-badge');
    const allTasks = [...tasks, ...completedTasks.map(t => ({ ...t, completed: 1 }))];

    // Сброс классов
    dayElement.classList.remove('has-tasks');

    if (allTasks.length === 0) {
        if (badge) badge.remove();
        return;
    }

    const day = parseInt(dayElement.querySelector('.day-link')?.getAttribute('data-day'));
    if (!day) return;

    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const taskDate = new Date(year, month - 1, day);

    // Подсчет невыполненных задач
    const incompleteTasks = tasks.filter(t => !t.completed);

    if (incompleteTasks.length > 0) {
        dayElement.classList.add('has-tasks');

        // Обновление бейджа
        const currentBadge = badge || (() => {
            const link = dayElement.querySelector('.day-link');
            if (!link) return null;
            const newBadge = document.createElement('span');
            newBadge.className = 'task-count-badge';
            link.appendChild(newBadge);
            return newBadge;
        })();

        if (currentBadge) {
            currentBadge.textContent = incompleteTasks.length;
            currentBadge.className = 'task-count-badge';

            const maxPriority = Math.max(...incompleteTasks.map(t => t.priority || 1));
            currentBadge.classList.add(
                maxPriority === 3 ? 'priority-high' :
                maxPriority === 2 ? 'priority-medium' : 'priority-low'
            );
        }
    } else if (badge) {
        badge.remove();
    }
}

export function initFilters() {
    const categoryFilter = document.getElementById('category-filter');
    const priorityFilter = document.getElementById('priority-filter');

    if (categoryFilter) {
        categoryFilter.addEventListener('change', applyFilters);
    }

    if (priorityFilter) {
        priorityFilter.addEventListener('change', applyFilters);
    }

    // Первоначальное применение фильтров
    setTimeout(applyFilters, 100);
}