export function applyFilters() {
    const categoryFilter = document.getElementById('category-filter')?.value;
    const priorityFilter = document.getElementById('priority-filter')?.value;

    document.querySelectorAll('.task-item, .completed-task-item').forEach(item => {
        const itemCategories = item.dataset.categories ? item.dataset.categories.split(',') : [];
        const itemPriority = item.dataset.priority;
        const categoryMatch = !categoryFilter || itemCategories.includes(categoryFilter);
        const priorityMatch = !priorityFilter || itemPriority === priorityFilter;
        item.style.display = (categoryMatch && priorityMatch) ? '' : 'none';
    });
}