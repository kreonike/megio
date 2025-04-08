// static/js/remind.js
export function bindRemindHandlers(year, month) {
    console.log('[bindRemindHandlers] Binding remind handlers');
    document.querySelectorAll('.remind-btn').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            console.log(`[bindRemindHandlers] Remind button clicked for task ${taskId}`);
            toggleRemindForm(taskId);
        });
    });

    document.querySelectorAll('.remind-form .cancel-remind').forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.closest('.remind-form').getAttribute('data-task-id');
            console.log(`[bindRemindHandlers] Cancel remind for task ${taskId}`);
            toggleRemindForm(taskId);
        });
    });

    document.querySelectorAll('.remind-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const taskId = this.getAttribute('data-task-id');
            console.log(`[bindRemindHandlers] Submitting remind form for task ${taskId}`);
            submitRemindForm(taskId, year, month);
        });
    });
}

function toggleRemindForm(taskId) {
    const remindForm = document.getElementById(`remind-form-${taskId}`);
    if (remindForm) {
        const isActive = remindForm.classList.contains('active');
        remindForm.classList.toggle('active', !isActive);
        console.log(`[toggleRemindForm] Toggled remind form for task ${taskId} to ${!isActive ? 'visible' : 'hidden'}`);
    }
}

function submitRemindForm(taskId, year, month) {
    const form = document.getElementById(`remind-form-${taskId}`);
    const remindOptions = Array.from(form.querySelectorAll('input[name="remind-options"]:checked')).map(input => input.value);
    console.log(`[submitRemindForm] Selected remind options for task ${taskId}:`, remindOptions);

    fetch(`/tasks/${year}/${month}/remind`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            task_id: taskId,
            remind_options: remindOptions
        })
    })
    .then(response => {
        if (!response.ok) {
            console.error('[submitRemindForm] Network response not ok:', response.status);
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('[submitRemindForm] Remind response:', data);
        if (data.success) {
            console.log(`[submitRemindForm] Reminder set successfully for task ${taskId}`);
            toggleRemindForm(taskId); // Скрываем форму после успешной отправки
        } else {
            console.error('[submitRemindForm] Failed to set reminder:', data.error);
        }
    })
    .catch(error => {
        console.error('[submitRemindForm] Error setting reminder:', error);
    });
}