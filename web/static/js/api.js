export async function fetchTasks(year, month, day) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`[api/fetchTasks] Error for ${year}-${month}-${day}:`, error);
        throw error;
    }
}

export async function addTask(year, month, day, taskData) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(taskData)
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`[api/addTask] Error for ${year}-${month}-${day}:`, error);
        throw error;
    }
}

export async function completeTask(taskId, year, month, day) {
    try {
        if (!year || !month || !day || year === 'undefined' || month === 'undefined' || day === 'undefined') {
            throw new Error(`Invalid parameters: year=${year}, month=${month}, day=${day}`);
        }
        console.log(`[api/completeTask] Sending request for task ${taskId} on ${year}-${month}-${day}`);
        const response = await fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ complete: taskId })
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`[api/completeTask] Error for task ${taskId}:`, error);
        throw error;
    }
}

export async function fetchCompletedTasks(year, month, day) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}/completed`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`[api/fetchCompletedTasks] Error for ${year}-${month}-${day}:`, error);
        throw error;
    }
}

export async function fetchMonthTasks(year, month) {
    try {
        const response = await fetch(`/tasks/${year}/${month}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`[api/fetchMonthTasks] Error for ${year}-${month}:`, error);
        throw error;
    }
}