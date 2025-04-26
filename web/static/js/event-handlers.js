import { updateTasksSection } from './tasks-module.js';
import { updateTaskPriorityIndicator, updateCalendar } from './calendar-module.js';
import { fetchTasks, fetchCompletedTasks, restoreTask, completeTask, deleteTask, setReminders, createTask, updateTask } from './api.js';
import { bindTimeSpinnerEvents, formatDateForInput } from './utils.js';
import { applyFilters } from './filters.js';

export function bindDayClickHandlers(year, month) {
    console.log(`[event-handlers/bindDayClickHandlers] Binding handlers for ${year}-${month}`);
    const links = document.querySelectorAll('.day-link');
    if (!links.length) {
        console.error('[event-handlers/bindDayClickHandlers] No day links found in DOM');
        return;
    }
    links.forEach(link => {
        link.removeEventListener('click', handleDayClick);
        link.addEventListener('click', handleDayClick);
    });

    async function handleDayClick(e) {
        e.preventDefault();
        console.log('[event-handlers/handleDayClick] Day link clicked:', this);
        document.querySelectorAll('.day-link').forEach(l => l.classList.remove('selected'));
        this.classList.add('selected');
        const dayAttr = this.getAttribute('data-day');
        if (!dayAttr || isNaN(dayAttr)) {
            console.error('[event-handlers/handleDayClick] Inactive day link:', dayAttr);
            alert('Ошибка: некорректный день');
            return;
        }

        const date = `${year}-${String(month).padStart(2, '0')}-${String(dayAttr).padStart(2, '0')}`;
        console.log('[event-handlers/handleDayClick] Fetching tasks for:', date);

        const tasksSection = document.querySelector('.tasks-section');
        if (!tasksSection) {
            console.error('[event-handlers/handleDayClick] Tasks section not found in DOM');
            alert('Ошибка: секция задач не найдена');
            return;
        }
        tasksSection.innerHTML = '<p>Загрузка...</p>';

        try {
            const [taskData, completedTasks] = await Promise.all([
                fetchTasks(year, month, dayAttr),
                fetchCompletedTasks(year, month, dayAttr)
            ]);
            console.log('[event-handlers/handleDayClick] Task data:', taskData, 'Completed tasks:', completedTasks);
            if (taskData.success && taskData.data) {
                updateTasksSection(
                    taskData.data.tasks || [],
                    completedTasks || [],
                    date,
                    parseInt(dayAttr),
                    taskData.data.categories || []
                );
                bindTaskEventHandlers(year, month, parseInt(dayAttr));
                updateTaskPriorityIndicator(
                    this.closest('.day-cell'),
                    taskData.data.tasks || [],
                    completedTasks || []
                );
            } else {
                console.error('[event-handlers/handleDayClick] Invalid task response:', taskData);
                tasksSection.innerHTML = '<p>Ошибка загрузки задач</p>';
            }
        } catch (error) {
            console.error('[event-handlers/handleDayClick] Error:', error);
            tasksSection.innerHTML = '<p>Ошибка загрузки задач: ' + error.message + '</p>';
        }
    }
}

export function bindTaskEventHandlers(year, month, day) {
    console.log(`[event-handlers/bindTaskEventHandlers] Binding task handlers for ${year}-${month}-${day}`);

    // Привязываем обработчики ко всем полям ввода времени
    const timeInputs = document.querySelectorAll('.time-input, .edit-time-input');
    timeInputs.forEach(input => {
        if (!input.dataset.spinnerBound) {
            bindTimeSpinnerEvents(input);
            input.dataset.spinnerBound = 'true';
        }
    });

    const mainRepeatCheckbox = document.getElementById('main-repeat-checkbox');
    if (mainRepeatCheckbox) {
        mainRepeatCheckbox.addEventListener('change', function (e) {
            e.stopPropagation();
            const details = this.closest('.repeat-options')?.querySelector('.repeat-details');
            if (details) {
                details.style.display = this.checked ? 'block' : 'none';
                if (!this.checked) {
                    details.querySelector('input[name="repeat_days"]').value = '1';
                    details.querySelector('input[name="repeat_start"]').value = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                    details.querySelector('input[name="repeat_end"]').value = '';
                }
            }
        });
    }

    document.querySelectorAll('.edit-repeat-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function (e) {
            e.stopPropagation();
            const details = this.closest('.repeat-options')?.querySelector('.repeat-details');
            if (details) {
                details.style.display = this.checked ? 'block' : 'none';
                if (!this.checked) {
                    details.querySelector('input[name="repeat_days"]').value = '1';
                    details.querySelector('input[name="repeat_start"]').value = formatDateForInput(new Date());
                    details.querySelector('input[name="repeat_end"]').value = '';
                }
            }
        });
    });

    const categoryFilter = document.getElementById('category-filter');
    const priorityFilter = document.getElementById('priority-filter');
    if (categoryFilter) categoryFilter.addEventListener('change', applyFilters);
    if (priorityFilter) priorityFilter.addEventListener('change', applyFilters);

    document.querySelectorAll('.remind-btn').forEach(button => {
        button.addEventListener('click', function (e) {
            e.stopPropagation();
            const taskId = this.getAttribute('data-task-id');
            const remindForm = document.getElementById(`remind-form-${taskId}`);
            document.querySelectorAll('.remind-form.active, .edit-form.active').forEach(form => {
                if (form !== remindForm) form.classList.remove('active');
            });
            if (remindForm) remindForm.classList.toggle('active');
        });
    });

    document.querySelectorAll('.remind-confirm-btn').forEach(button => {
        button.addEventListener('click', async function () {
            const taskId = this.getAttribute('data-task-id');
            const remindForm = this.closest('.remind-form');
            if (!remindForm) return;
            const selectedReminders = Array.from(
                remindForm.querySelectorAll('input[name="remind_times"]:checked')
            ).map(el => parseInt(el.value));

            if (selectedReminders.length === 0) {
                alert('Выберите хотя бы одно время напоминания');
                return;
            }

            try {
                const data = await setReminders(year, month, day, taskId, selectedReminders);
                if (data.success) {
                    remindForm.classList.remove('active');
                    console.log('[event-handlers/remind] Reminders set for task', taskId);
                } else {
                    console.error('[event-handlers/remind] Error:', data.error);
                    alert('Ошибка при установке напоминаний: ' + data.error);
                }
            } catch (error) {
                console.error('[event-handlers/remind] Error:', error);
                alert('Ошибка при отправке запроса');
            }
        });
    });

    document.querySelectorAll('.cancel-remind').forEach(button => {
        button.addEventListener('click', function () {
            const remindForm = this.closest('.remind-form');
            if (remindForm) remindForm.classList.remove('active');
        });
    });

    document.querySelectorAll('.edit-btn').forEach(button => {
        button.addEventListener('click', function (e) {
            e.stopPropagation();
            const taskId = this.getAttribute('data-task-id');
            const editForm = document.getElementById(`edit-form-${taskId}`);
            document.querySelectorAll('.edit-form.active, .remind-form.active').forEach(form => {
                if (form !== editForm) form.classList.remove('active');
            });
            if (editForm) editForm.classList.toggle('active');
        });
    });

    document.querySelectorAll('.cancel-edit').forEach(button => {
        button.addEventListener('click', function () {
            const editForm = this.closest('.edit-form');
            if (editForm) editForm.classList.remove('active');
        });
    });

    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', async function () {
            if (!confirm('Вы уверены, что хотите удалить эту задачу?')) return;
            const taskId = this.getAttribute('data-task-id');

            try {
                const data = await deleteTask(year, month, day, taskId);
                if (data.success) {
                    const [taskData, completedTasks] = await Promise.all([
                        fetchTasks(year, month, day),
                        fetchCompletedTasks(year, month, day)
                    ]);
                    if (taskData.success && taskData.data) {
                        updateTasksSection(
                            taskData.data.tasks || [],
                            completedTasks || [],
                            `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
                            day,
                            taskData.data.categories || []
                        );
                        bindTaskEventHandlers(year, month, day);
                        await updateCalendar(year, month);
                        bindDayClickHandlers(year, month);
                    }
                } else {
                    alert('Ошибка при удалении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            } catch (error) {
                console.error('[event-handlers/delete] Error:', error);
                alert('Ошибка при удалении задачи');
            }
        });
    });

    document.querySelectorAll('.complete-btn').forEach(button => {
        button.addEventListener('click', async function () {
            const taskId = this.getAttribute('data-task-id');

            try {
                const data = await completeTask(year, month, day, taskId);
                if (data.success) {
                    const [taskData, completedTasks] = await Promise.all([
                        fetchTasks(year, month, day),
                        fetchCompletedTasks(year, month, day)
                    ]);
                    if (taskData.success && taskData.data) {
                        updateTasksSection(
                            taskData.data.tasks || [],
                            completedTasks,
                            `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
                            day,
                            taskData.data.categories || []
                        );
                        bindTaskEventHandlers(year, month, day);
                        await updateCalendar(year, month);
                        bindDayClickHandlers(year, month);
                    }
                } else {
                    alert('Ошибка при выполнении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            } catch (error) {
                console.error('[event-handlers/complete] Error:', error);
                alert('Ошибка при выполнении задачи');
            }
        });
    });

    document.querySelectorAll('.restore-btn').forEach(button => {
        button.addEventListener('click', async function (e) {
            e.preventDefault();
            const taskId = this.getAttribute('data-task-id');
            console.log(`[event-handlers/handleRestore] Restoring task ${taskId}`);

            if (!taskId) {
                console.error('[event-handlers/handleRestore] No taskId found');
                alert('Ошибка: ID задачи не найден');
                return;
            }

            try {
                const data = await restoreTask(year, month, day, taskId);
                if (data.success) {
                    console.log(`[event-handlers/handleRestore] Task ${taskId} restored`);
                    const [taskData, completedTasks] = await Promise.all([
                        fetchTasks(year, month, day),
                        fetchCompletedTasks(year, month, day)
                    ]);
                    if (taskData.success && taskData.data) {
                        updateTasksSection(
                            taskData.data.tasks || [],
                            completedTasks,
                            `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
                            day,
                            taskData.data.categories || []
                        );
                        bindTaskEventHandlers(year, month, day);
                        await updateCalendar(year, month);
                        bindDayClickHandlers(year, month);
                    } else {
                        console.error('[event-handlers/handleRestore] Invalid task data:', taskData);
                        alert('Ошибка: некорректные данные после восстановления');
                    }
                } else {
                    console.error('[event-handlers/handleRestore] Restore failed:', data.error);
                    alert('Ошибка при восстановлении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            } catch (error) {
                console.error('[event-handlers/handleRestore] Error:', error);
                alert('Ошибка при восстановлении задачи: ' + error.message);
            }
        });
    });

    const taskForm = document.querySelector('.task-form');
    if (taskForm) {
        taskForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            try {
                const data = await createTask(year, month, day, new FormData(this));
                if (data.success) {
                    this.reset();
                    const [taskData, completedTasks] = await Promise.all([
                        fetchTasks(year, month, day),
                        fetchCompletedTasks(year, month, day)
                    ]);
                    if (taskData.success && taskData.data) {
                        updateTasksSection(
                            taskData.data.tasks || [],
                            completedTasks || [],
                            `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
                            day,
                            taskData.data.categories || []
                        );
                        bindTaskEventHandlers(year, month, day);
                        await updateCalendar(year, month);
                        bindDayClickHandlers(year, month);
                    }
                } else {
                    alert('Ошибка при добавлении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            } catch (error) {
                console.error('[event-handlers/task-form] Error:', error);
                alert('Ошибка при добавлении задачи');
            }
        });
    }

    document.querySelectorAll('.edit-form').forEach(form => {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            try {
                const data = await updateTask(year, month, day, new FormData(this));
                if (data.success) {
                    this.classList.remove('active');
                    const [taskData, completedTasks] = await Promise.all([
                        fetchTasks(year, month, day),
                        fetchCompletedTasks(year, month, day)
                    ]);
                    if (taskData.success && taskData.data) {
                        updateTasksSection(
                            taskData.data.tasks || [],
                            completedTasks || [],
                            `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
                            day,
                            taskData.data.categories || []
                        );
                        bindTaskEventHandlers(year, month, day);
                        await updateCalendar(year, month);
                        bindDayClickHandlers(year, month);
                    }
                } else {
                    alert('Ошибка при обновлении задачи: ' + (data.error || 'Неизвестная ошибка'));
                }
            } catch (error) {
                console.error('[event-handlers/edit-form] Error:', error);
                alert('Ошибка при обновлении задачи');
            }
        });
    });
}