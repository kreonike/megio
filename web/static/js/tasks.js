// static/js/tasks.js
import { updateTasksSection, updateCalendar } from './calendar-update.js';
import { formatDateForInput, bindTimeSpinnerEvents } from './time.js';

export function bindAllTaskHandlers(year, month) {
    console.log('[bindAllTaskHandlers] Binding all task handlers');
    bindTaskFormHandler(year, month);
    bindEditButtons(year, month);
    bindCancelEditButtons();
    bindDeleteButtons(year, month);
    bindCompleteButtons(year, month);
    bindRemindButtons(year, month);
    console.log('[bindAllTaskHandlers] All handlers bound');
}

function bindTaskFormHandler(year, month) {
    console.log('[bindTaskFormHandler] Initializing task form handler');
    const taskForm = document.querySelector('.task-form');
    if (!taskForm) {
        console.log('[bindTaskFormHandler] Task form not found');
        return;
    }

    const repeatCheckbox = taskForm.querySelector('#main-repeat-checkbox');
    const repeatDetails = taskForm.querySelector('.repeat-details');
    const repeatDaysInput = taskForm.querySelector('input[name="repeat_days"]');
    const repeatStartInput = taskForm.querySelector('input[name="repeat_start"]');
    const repeatEndInput = taskForm.querySelector('input[name="repeat_end"]');

    console.log('[bindTaskFormHandler] Repeat checkbox state:', {
        exists: !!repeatCheckbox,
        checked: repeatCheckbox ? repeatCheckbox.checked : null
    });
    console.log('[bindTaskFormHandler] Repeat elements:', {
        repeatCheckbox: !!repeatCheckbox,
        repeatDetails: !!repeatDetails,
        repeatDaysInput: !!repeatDaysInput,
        repeatStartInput: !!repeatStartInput,
        repeatEndInput: !!repeatEndInput
    });

    if (repeatCheckbox && repeatDetails) {
        console.log('[bindTaskFormHandler] Initializing repeat options');
        repeatCheckbox.addEventListener('change', function(e) {
            console.log('[RepeatCheckbox] Change event, checked:', this.checked);
            if (this.checked) {
                console.log('[RepeatCheckbox] Repeat enabled, setting default values');
                repeatDetails.style.display = 'block';
            } else {
                repeatDetails.style.display = 'none';
            }
        });
        repeatDetails.style.display = repeatCheckbox.checked ? 'block' : 'none';
    }

    taskForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('[TaskForm] Form submit triggered');

        const formData = new FormData(this);
        console.log('[TaskForm] Initial FormData:', Array.from(formData.entries()));

        if (repeatCheckbox && repeatCheckbox.checked) {
            console.log('[TaskForm] Processing repeat options, checkbox checked:', repeatCheckbox.checked);
            console.log('[TaskForm] Repeat enabled, setting values:', {
                days: repeatDaysInput.value,
                start: repeatStartInput.value,
                end: repeatEndInput.value
            });
        }

        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => {
            console.log('[TaskForm] Received response, status:', response.status);
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            console.log('[TaskForm] Response data:', data);
            if (data.status === 'success') {
                console.log('[TaskForm] Task saved successfully');
                taskForm.reset();
                if (repeatCheckbox && repeatDetails) {
                    console.log('[TaskForm] Resetting repeat checkbox');
                    repeatCheckbox.checked = false;
                    repeatDetails.style.display = 'none';
                    repeatDaysInput.value = '1';
                    repeatStartInput.value = formData.get('date');
                    repeatEndInput.value = '';
                }
                fetchTasks(year, month, parseInt(this.action.split('/').pop()));
                updateCalendar(year, month); // Добавляем обновление календаря
            }
        })
        .catch(error => {
            console.error('[TaskForm] Error submitting form:', error);
        });

        console.log('[TaskForm] Form submission handled');
    });

    console.log('[bindTaskFormHandler] Task form handler initialized');
}

function bindEditButtons(year, month) {
    document.querySelectorAll('.edit-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            console.log(`[EditButton] Edit button clicked for task ${taskId}`);
            const taskItem = this.closest('.task-item');
            const editForm = document.getElementById(`edit-form-${taskId}`);
            if (editForm && taskItem) {
                taskItem.classList.add('editing');
                editForm.style.display = 'block';
                const repeatCheckbox = editForm.querySelector('.edit-repeat-checkbox');
                const repeatDetails = editForm.querySelector('.repeat-details');
                if (repeatCheckbox && repeatDetails) {
                    console.log(`[EditForm] Initial repeat checkbox state for task ${taskId}:`, repeatCheckbox.checked);
                    repeatDetails.style.display = repeatCheckbox.checked ? 'block' : 'none';
                }
            }
        });
    });

    document.querySelectorAll('.edit-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            console.log('[EditForm] Edit form submit triggered');
            const formData = new FormData(this);
            const repeatCheckbox = form.querySelector('.edit-repeat-checkbox');

            // Если чекбокс снят, удаляем параметры повторения из FormData
            if (!repeatCheckbox.checked) {
                formData.delete('repeat_days');
                formData.delete('repeat_start');
                formData.delete('repeat_end');
                console.log('[EditForm] Repeat checkbox unchecked, removed repeat parameters');
            }

            console.log('[EditForm] FormData:', Array.from(formData.entries()));

            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => {
                console.log('[EditForm] Received response, status:', response.status);
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                console.log('[EditForm] Response data:', data);
                if (data.status === 'success') {
                    console.log('[EditForm] Task updated successfully');
                    fetchTasks(year, month, parseInt(this.action.split('/').pop()));
                    updateCalendar(year, month);
                }
            })
            .catch(error => {
                console.error('[EditForm] Error submitting edit form:', error);
            });
        });
    });
}

function bindCancelEditButtons() {
    document.querySelectorAll('.cancel-edit').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            console.log(`[CancelEdit] Cancel button clicked for task ${taskId}`);
            const taskItem = this.closest('.task-item');
            const editForm = document.getElementById(`edit-form-${taskId}`);
            if (editForm && taskItem) {
                editForm.style.display = 'none';
                taskItem.classList.remove('editing');
            }
        });
    });
}

function bindDeleteButtons(year, month) {
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            console.log(`[DeleteButton] Delete button clicked for task ${taskId}`);
            if (confirm('Вы уверены, что хотите удалить эту задачу?')) {
                fetch(`/tasks/${year}/${month}/${parseInt(document.querySelector('.task-date-header').textContent.split('.')[0])}`, {
                    method: 'POST',
                    body: new URLSearchParams({ 'delete': taskId }),
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => {
                    console.log('[DeleteButton] Received response, status:', response.status);
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    console.log('[DeleteButton] Response data:', data);
                    if (data.status === 'success') {
                        console.log('[DeleteButton] Task deleted successfully');
                        fetchTasks(year, month, parseInt(document.querySelector('.task-date-header').textContent.split('.')[0]));
                        updateCalendar(year, month); // Добавляем обновление календаря
                    }
                })
                .catch(error => {
                    console.error('[DeleteButton] Error deleting task:', error);
                });
            }
        });
    });
}

function bindCompleteButtons(year, month) {
    document.querySelectorAll('.complete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            console.log(`[CompleteButton] Complete button clicked for task ${taskId}`);
            fetch(`/tasks/${year}/${month}/${parseInt(document.querySelector('.task-date-header').textContent.split('.')[0])}/complete`, {
                method: 'POST',
                body: JSON.stringify({ task_id: taskId }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                console.log('[CompleteButton] Received response, status:', response.status);
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                console.log('[CompleteButton] Response data:', data);
                if (data.success) {
                    console.log('[CompleteButton] Task completed successfully');
                    fetchTasks(year, month, parseInt(document.querySelector('.task-date-header').textContent.split('.')[0]));
                    updateCalendar(year, month); // Добавляем обновление календаря
                }
            })
            .catch(error => {
                console.error('[CompleteButton] Error completing task:', error);
            });
        });
    });
}

function bindRemindButtons(year, month) {
    document.querySelectorAll('.remind-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            console.log(`[RemindButton] Remind button clicked for task ${taskId}`);
            const remindTimes = prompt('Введите время напоминаний (в минутах, через запятую, например: 15, 120, 1440):');
            if (remindTimes) {
                const timesArray = remindTimes.split(',').map(t => parseInt(t.trim())).filter(t => !isNaN(t));
                fetch(`/tasks/${year}/${month}/${parseInt(document.querySelector('.task-date-header').textContent.split('.')[0])}/remind`, {
                    method: 'POST',
                    body: JSON.stringify({ task_id: taskId, remind_times: timesArray }),
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    console.log('[RemindButton] Received response, status:', response.status);
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    console.log('[RemindButton] Response data:', data);
                    if (data.success) {
                        console.log('[RemindButton] Reminders set successfully');
                        // Нет необходимости обновлять календарь, так как напоминания не влияют на значки
                    }
                })
                .catch(error => {
                    console.error('[RemindButton] Error setting reminders:', error);
                });
            }
        });
    });
}

function fetchTasks(year, month, day) {
    console.log(`[fetchTasks] Fetching tasks for ${year}-${month}-${day}`);
    fetch(`/tasks/${year}/${month}/${day}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        console.log('[fetchTasks] Received response, status:', response.status);
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        console.log('[fetchTasks] Received tasks data:', data);
        updateTasksSection(data.tasks, data.date, day, data.categories);
    })
    .catch(error => {
        console.error('[fetchTasks] Error fetching tasks:', error);
    });
}