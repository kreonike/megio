export function initFilters() {
    const categoryFilter = document.getElementById('category-filter');
    const priorityFilter = document.getElementById('priority-filter');

    if (!categoryFilter || !priorityFilter) {
        console.warn('[filters/initFilters] Category or priority filter not found');
        return;
    }

    // Bind event listeners
    categoryFilter.addEventListener('change', applyFilters);
    priorityFilter.addEventListener('change', applyFilters);

    // Apply filters immediately if there are initial values
    applyFilters();
}

export function applyFilters() {
    const categoryFilter = document.getElementById('category-filter')?.value;
    const priorityFilter = document.getElementById('priority-filter')?.value;

    document.querySelectorAll('.task, .completed-task').forEach(item => {
        const itemCategories = item.dataset.categories ? item.dataset.categories.split(',') : [];
        const itemPriority = item.dataset.priority;
        const categoryMatch = !categoryFilter || itemCategories.includes(categoryFilter);
        const priorityMatch = !priorityFilter || itemPriority === priorityFilter;
        item.style.display = (categoryMatch && priorityMatch) ? '' : 'none';
    });
}