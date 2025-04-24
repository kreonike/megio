// static/js/api.js
export async function fetchTasks(year, month, day) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        console.log(`[api/fetchTasks] Response status for ${year}-${month}-${day}:`, response.status);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        if (!data.success || !data.data) {
            console.warn(`[api/fetchTasks] Invalid response data for ${year}-${month}-${day}:`, data);
            return { success: false, data: null };
        }
        return data;
    } catch (error) {
        console.error(`[api/fetchTasks] Error for ${year}-${month}-${day}:`, error);
        return { success: false, data: null };
    }
}

export async function fetchMonthTasks(year, month) {
    try {
        const response = await fetch(`/tasks/${year}/${month}`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        console.log(`[api/fetchMonthTasks] Response status for ${year}-${month}:`, response.status);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        if (!data.success || !data.data) {
            console.warn(`[api/fetchMonthTasks] Invalid response data for ${year}-${month}:`, data);
            return { success: false, data: null };
        }
        return data;
    } catch (error) {
        console.error(`[api/fetchMonthTasks] Error for ${year}-${month}:`, error);
        return { success: false, data: null };
    }
}

export async function fetchCompletedTasks(year, month, day) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}/completed`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        console.log(`[api/fetchCompletedTasks] Response status for ${year}-${month}-${day}:`, response.status);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        console.log(`[api/fetchCompletedTasks] Data for ${year}-${month}-${day}:`, JSON.stringify(data, null, 2));
        if (!data.success || !data.data) {
            console.warn(`[api/fetchCompletedTasks] Invalid response data for ${year}-${month}-${day}:`, data);
            return [];
        }
        const completedTasks = data.data.completedTasks || [];
        return completedTasks;
    } catch (error) {
        console.error(`[api/fetchCompletedTasks] Error for ${year}-${month}-${day}:`, error);
        return [];
    }
}

export async function restoreTask(year, month, day, taskId) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}/restore`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ completed_task_id: taskId })
        });
        if (!response.ok) {
            if (response.status === 404) throw new Error('Задача не найдена в завершённых');
            if (response.status === 409) throw new Error('Задача уже восстановлена');
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`[api/restoreTask] Error for task ${taskId}:`, error);
        throw error;
    }
}

export async function completeTask(year, month, day, taskId) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ task_id: taskId })
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`[api/completeTask] Error for task ${taskId}:`, error);
        throw error;
    }
}

export async function deleteTask(year, month, day, taskId) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `delete=${taskId}`
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`[api/deleteTask] Error for task ${taskId}:`, error);
        throw error;
    }
}

export async function setReminders(year, month, day, taskId, remindTimes) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}/remind`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ task_id: taskId, remind_times: remindTimes })
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`[api/setReminders] Error for task ${taskId}:`, error);
        throw error;
    }
}

export async function createTask(year, month, day, formData) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`[api/createTask] Error:`, error);
        throw error;
    }
}

export async function updateTask(year, month, day, formData) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`[api/updateTask] Error:`, error);
        throw error;
    }
}