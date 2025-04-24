import { updateTasksSection, updateCalendar, updateTaskPriorityIndicator } from './calendar-update.js';
import { formatDateForInput, bindTimeSpinnerEvents } from './time.js';
import { fetchCompletedTasks } from './completed-tasks.js';

export function bindAllTaskHandlers(year, month) {
    console.log(`[bindAllTaskHandlers] Binding all task handlers for ${year}-${month}`);
    bindTaskFormHandler(year, month);
    bindEditButtons(year, month);
    bindCancelEditButtons();
    bindDeleteButtons(year, month);
    bindCompleteButtons(year, month);
    bindRemindButtons(year, month);
    bindDayClickHandlers(year, month);
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

    console.log('[bindTaskFormHandler] Repeat elements:', {
        repeatCheckbox: !!repeatCheckbox,
        repeatDetails: !!repeatDetails,
        repeatDaysInput: !!repeatDaysInput,
        repeatStartInput: !!repeatStartInput,
        repeatEndInput: !!repeatEndInput
    });

    if (repeatCheckbox && repeatDetails) {
        console.log('[bindTaskFormHandler] Initializing repeat options');
        repeatDetails.style.display = repeatCheckbox.checked ? 'block' : 'none';
        repeatCheckbox.addEventListener('change', function(e) {
            console.log('[RepeatCheckbox] Change event, checked:', this.checked);
            repeatDetails.style.display = this.checked ? 'block' : 'none';
        });
    }

    taskForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log('[TaskForm] Form submit triggered');

        const formData = new FormData(this);
        console.log('[TaskForm] FormData:', Array.from(formData.entries()));

        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => {
            console.log('[TaskForm] Response status:', response.status);
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('[TaskForm] Response data:', data);
            if (data.success) {
                console.log('[TaskForm] Task saved successfully');
                taskForm.reset();
                if (repeatCheckbox && repeatDetails) {
                    repeatCheckbox.checked = false;
                    repeatDetails.style.display = 'none';
                    repeatDaysInput.value = '1';
                    repeatStartInput.value = formData.get('date');
                    repeatEndInput.value = '';
                }
                const day = parseInt(this.action.split('/').pop());
                fetchTasks(year, month, day);
                updateCalendar(year, month);
            } else {
                console.error('[TaskForm] Error:', data.error);
                alert('Ошибка при добавлении задачи: ' + (data.error || 'Неизвестная ошибка'));
            }
        })
        .catch(error => {
            console.error('[TaskForm] Error submitting form:', error);
            alert('Ошибка при добавлении задачи: ' + error.message);
        });
    });

    // Привязываем спиннер времени
    const taskTimeInput = taskForm.querySelector('#task-time');
    if (taskTimeInput) {
        bindTimeSpinnerEvents(taskTimeInput);
    }
}

function bindEditButtons(year, month) {
    document.querySelectorAll('.edit-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const taskId = this.getAttribute('data-task-id');
            console.log(`[EditButton] Edit button clicked for task ${taskId}`);
            const editForm = document.getElementById(`edit-form-${taskId}`);
            if (editForm) {
                document.querySelectorAll('.edit-form.active, .remind-form.active').forEach(form => {
                    if (form !== editForm) form.classList.remove('active');
                });
                editForm.classList.toggle('active');
                const repeatCheckbox = editForm.querySelector('.edit-repeat-checkbox');
                const repeatDetails = editForm.querySelector('.repeat-details');
                if (repeatCheckbox && repeatDetails) {
                    console.log(`[EditForm] Repeat checkbox state for task ${taskId}:`, repeatCheckbox.checked);
                    repeatDetails.style.display = repeatCheckbox.checked ? 'block' : 'none';
                    repeatCheckbox.addEventListener('change', function() {
                        repeatDetails.style.display = this.checked ? 'block' : 'none';
                    });
                }
                // Привязываем спиннер времени для формы редактирования
                const editTimeInput = editForm.querySelector('.edit-time-input');
                if (editTimeInput) {
                    bindTimeSpinnerEvents(editTimeInput);
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
            if (!repeatCheckbox.checked) {
                formData.delete('repeat_days');
                formData.delete('repeat_start');
                formData.delete('repeat_end');
                console.log('[EditForm] Repeat unchecked, removed repeat parameters');
            }
            console.log('[EditForm] FormData:', Array.from(formData.entries()));

            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => {
                console.log('[EditForm] Response status:', response.status);
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                console.log('[EditForm] Response data:', data);
                if (data.success) {
                    console.log('[EditForm] Task updated successfully');
                    form.classList.remove('active');
                    const day = parseInt(this.action.split('/').pop());
                    fetchTasks(year, month, day);
                    updateCalendar(year, month);
                } else {
                    console.error('[EditForm] Error:', data.error);
                    alert('Ошибка при обновлении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('[EditForm] Error submitting edit form:', error);
                alert('Ошибка при обновлении задачи: ' + error.message);
            });
        });
    });
}

function bindCancelEditButtons() {
    document.querySelectorAll('.cancel-edit').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const taskId = this.getAttribute('data-task-id');
            console.log(`[CancelEdit] Cancel button clicked for task ${taskId}`);
            const editForm = document.getElementById(`edit-form-${taskId}`);
            if (editForm) {
                editForm.classList.remove('active');
            }
        });
    });
}

function bindDeleteButtons(year, month) {
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const taskId = this.getAttribute('data-task-id');
            console.log(`[DeleteButton] Delete button clicked for task ${taskId}`);
            if (!confirm('Вы уверены, что хотите удалить эту задачу?')) return;

            const taskDateHeader = document.querySelector('.task-date-header');
            const day = taskDateHeader ? parseInt(taskDateHeader.textContent.split('.')[0]) : null;
            if (!day) {
                console.error('[DeleteButton] Could not determine day from task-date-header');
                alert('Ошибка: не удалось определить дату');
                return;
            }

            fetch(`/tasks/${year}/${month}/${day}`, {
                method: 'POST',
                body: new URLSearchParams({ 'delete': taskId }),
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => {
                console.log('[DeleteButton] Response status:', response.status);
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                console.log('[DeleteButton] Response data:', data);
                if (data.success) {
                    console.log('[DeleteButton] Task deleted successfully');
                    fetchTasks(year, month, day);
                    updateCalendar(year, month);
                } else {
                    console.error('[DeleteButton] Error:', data.error);
                    alert('Ошибка при удалении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('[DeleteButton] Error deleting task:', error);
                alert('Ошибка при удалении задачи: ' + error.message);
            });
        });
    });
}

function bindCompleteButtons(year, month) {
    document.querySelectorAll('.complete-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const taskId = this.getAttribute('data-task-id');
            console.log(`[CompleteButton] Complete button clicked for task ${taskId}`);

            const taskDateHeader = document.querySelector('.task-date-header');
            const day = taskDateHeader ? parseInt(taskDateHeader.textContent.split('.')[0]) : null;
            if (!day) {
                console.error('[CompleteButton] Could not determine day from task-date-header');
                alert('Ошибка: не удалось определить дату');
                return;
            }

            fetch(`/tasks/${year}/${month}/${day}/complete`, {
                method: 'POST',
                body: JSON.stringify({ task_id: taskId }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                console.log('[CompleteButton] Response status:', response.status);
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                console.log('[CompleteButton] Response data:', data);
                if (data.success) {
                    console.log('[CompleteButton] Task completed successfully');
                    fetchTasks(year, month, day);
                    updateCalendar(year, month);
                    fetchCompletedTasks(year, month, day);
                } else {
                    console.error('[CompleteButton] Error:', data.error);
                    alert('Ошибка при выполнении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('[CompleteButton] Error completing task:', error);
                alert('Ошибка при выполнении задачи: ' + error.message);
            });
        });
    });
}

function bindRemindButtons(year, month) {
    document.querySelectorAll('.remind-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const taskId = this.getAttribute('data-task-id');
            console.log(`[RemindButton] Remind button clicked for task ${taskId}`);
            const remindForm = document.getElementById(`remind-form-${taskId}`);
            if (remindForm) {
                document.querySelectorAll('.remind-form.active, .edit-form.active').forEach(form => {
                    if (form !== remindForm) form.classList.remove('active');
                });
                remindForm.classList.toggle('active');
            }
        });
    });

    document.querySelectorAll('.remind-confirm-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const taskId = this.getAttribute('data-task-id');
            console.log(`[RemindConfirm] Confirm button clicked for task ${taskId}`);
            const remindForm = this.closest('.remind-form');
            const selectedReminders = Array.from(
                remindForm.querySelectorAll('input[name="remind_times"]:checked')
            ).map(el => parseInt(el.value));

            if (selectedReminders.length === 0) {
                alert('Пожалуйста, выберите хотя бы одно время напоминания');
                return;
            }

            const taskDateHeader = document.querySelector('.task-date-header');
            const day = taskDateHeader ? parseInt(taskDateHeader.textContent.split('.')[0]) : null;
            if (!day) {
                console.error('[RemindConfirm] Could not determine day from task-date-header');
                alert('Ошибка: не удалось определить дату');
                return;
            }

            fetch(`/tasks/${year}/${month}/${day}/remind`, {
                method: 'POST',
                body: JSON.stringify({ task_id: taskId, remind_times: selectedReminders }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                console.log('[RemindConfirm] Response status:', response.status);
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                console.log('[RemindConfirm] Response data:', data);
                if (data.success) {
                    console.log('[RemindConfirm] Reminders set successfully');
                    remindForm.classList.remove('active');
                } else {
                    console.error('[RemindConfirm] Error:', data.error);
                    alert('Ошибка при установке напоминаний: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('[RemindConfirm] Error setting reminders:', error);
                alert('Ошибка при установке напоминаний: ' + error.message);
            });
        });
    });

    document.querySelectorAll('.cancel-remind').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            console.log('[RemindCancel] Cancel remind button clicked');
            this.closest('.remind-form').classList.remove('active');
        });
    });
}

function bindDayClickHandlers(year, month) {
    console.log(`[bindDayClickHandlers] Binding day click handlers for ${year}-${month}`);
    document.querySelectorAll('.day-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('[DayClick] Day clicked:', this.getAttribute('data-day'));
            document.querySelectorAll('.day-link').forEach(l => l.classList.remove('selected'));
            this.classList.add('selected');

            const day = parseInt(this.getAttribute('data-day'));
            if (isNaN(day)) {
                console.error('[DayClick] Invalid day value:', this.getAttribute('data-day'));
                return;
            }

            const date = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const tasksSection = document.querySelector('.tasks-section');
            if (tasksSection) {
                tasksSection.innerHTML = '<p>Загрузка...</p>';
            }

            fetch(`/tasks/${year}/${month}/${day}`, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => {
                console.log('[DayClick] Response status:', response.status);
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                return response.json();
            })
            .then(data => {
                console.log('[DayClick] Response data:', data);
                if (data.success && data.data) {
                    updateTasksSection(data.data.tasks || [], date, day, data.data.categories || [], year, month);
                    const dayCell = this.closest('.day-cell');
                    if (dayCell) {
                        updateTaskPriorityIndicator(dayCell, data.data.tasks || []);
                    } else {
                        console.warn('[DayClick] No day-cell found for day:', day);
                    }
                    fetchCompletedTasks(year, month, day);
                } else {
                    console.error('[DayClick] Invalid response data:', data);
                    alert('Ошибка: сервер вернул некорректные данные');
                    if (tasksSection) {
                        tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
                    }
                }
            })
            .catch(error => {
                console.error('[DayClick] Error loading tasks:', error);
                alert('Ошибка при загрузке задач: ' + error.message);
                if (tasksSection) {
                    tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
                }
            });
        });
    });
}

function fetchTasks(year, month, day) {
    console.log(`[fetchTasks] Fetching tasks for ${year}-${month}-${day}`);
    fetch(`/tasks/${year}/${month}/${day}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        console.log('[fetchTasks] Response status:', response.status);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('[fetchTasks] Response data:', data);
        if (data.success && data.data) {
            const date = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            updateTasksSection(data.data.tasks || [], date, day, data.data.categories || [], year, month);
            fetchCompletedTasks(year, month, day);
        } else {
            console.error('[fetchTasks] Invalid response data:', data);
            alert('Ошибка: сервер вернул некорректные данные');
            const tasksSection = document.querySelector('.tasks-section');
            if (tasksSection) {
                tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
            }
        }
    })
    .catch(error => {
        console.error('[fetchTasks] Error fetching tasks:', error);
        alert('Ошибка при загрузке задач: ' + error.message);
        const tasksSection = document.querySelector('.tasks-section');
        if (tasksSection) {
            tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
        }
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = today.getMonth() + 1;
    const day = today.getDate();
    console.log(`[DOMContentLoaded] Initializing for ${year}-${month}-${day}`);

    // Инициализация календаря
    updateCalendar(year, month)
        .then(() => console.log('[DOMContentLoaded] Calendar initialized'))
        .catch(err => console.error('[DOMContentLoaded] Error initializing calendar:', err));

    // Загрузка задач для текущего дня
    fetchTasks(year, month, day);

    // Выделение текущего дня
    const todayLink = document.querySelector(`.day-link[data-day="${day}"]`);
    if (todayLink) {
        todayLink.classList.add('selected');
    }
});