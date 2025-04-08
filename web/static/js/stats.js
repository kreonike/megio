// static/js/stats.js
document.addEventListener('DOMContentLoaded', () => {
    // Применение фильтров
    const applyFiltersButton = document.getElementById('apply-filters');
    applyFiltersButton.addEventListener('click', () => {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        const priority = document.getElementById('priority-filter').value;

        fetchStats(startDate, endDate, priority);
        fetchTasks(startDate, endDate, priority);
    });

    // Сортировка таблицы
    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const column = th.dataset.column;
            const isAsc = th.classList.contains('sorted-asc');
            sortTable(column, !isAsc);
            updateSortIndicators(th, !isAsc);
        });
    });
});

function fetchStats(startDate, endDate, priority) {
    const url = new URL('/stats', window.location.origin);
    if (startDate) url.searchParams.append('start_date', startDate);
    if (endDate) url.searchParams.append('end_date', endDate);
    if (priority) url.searchParams.append('priority', priority);

    fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        const tbody = document.getElementById('stats-table-body');
        tbody.innerHTML = '';

        if (data.stats.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="no-data">Нет данных за выбранный период</td></tr>';
        } else {
            data.stats.forEach(stat => {
                tbody.innerHTML += `
                    <tr>
                        <td>${stat.month}</td>
                        <td><span class="stat-value">${stat.total}</span></td>
                        <td><span class="stat-value priority-high">${stat.high_priority}</span></td>
                        <td><span class="stat-value priority-medium">${stat.medium_priority}</span></td>
                        <td><span class="stat-value priority-low">${stat.low_priority}</span></td>
                    </tr>
                `;
            });
        }
    })
    .catch(error => console.error('Error fetching stats:', error));
}

function fetchTasks(startDate, endDate, priority) {
    const url = new URL('/stats/tasks', window.location.origin);
    if (startDate) url.searchParams.append('start_date', startDate);
    if (endDate) url.searchParams.append('end_date', endDate);
    if (priority) url.searchParams.append('priority', priority);

    fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        const tasksList = document.getElementById('tasks-list');
        tasksList.innerHTML = '';

        if (data.tasks.length === 0) {
            tasksList.innerHTML = '<li class="no-data">Нет выполненных задач за выбранный период</li>';
        } else {
            data.tasks.forEach(task => {
                const priorityClass = task.priority === 3 ? 'priority-high' :
                                     task.priority === 2 ? 'priority-medium' : 'priority-low';
                tasksList.innerHTML += `
                    <li>
                        <span class="task-priority-icon ${priorityClass}"></span>
                        <span class="task-completion-time">${new Date(task.completion_time).toLocaleString()}</span>
                        <span class="task-text">${task.task_text}</span>
                    </li>
                `;
            });
        }
    })
    .catch(error => console.error('Error fetching tasks:', error));
}

function sortTable(column, ascending) {
    const tbody = document.getElementById('stats-table-body');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        let aValue = a.children[[...a.parentElement.children[0].children].indexOf(
            document.querySelector(`[data-column="${column}"]`)
        )].textContent;
        let bValue = b.children[[...b.parentElement.children[0].children].indexOf(
            document.querySelector(`[data-column="${column}"]`)
        )].textContent;

        if (column !== 'month') {
            aValue = parseInt(aValue) || 0;
            bValue = parseInt(bValue) || 0;
            return ascending ? aValue - bValue : bValue - aValue;
        }
        return ascending ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
    });

    rows.forEach(row => tbody.appendChild(row));
}

function updateSortIndicators(th, ascending) {
    document.querySelectorAll('.sortable').forEach(header => {
        header.classList.remove('sorted-asc', 'sorted-desc');
    });
    th.classList.add(ascending ? 'sorted-asc' : 'sorted-desc');
}