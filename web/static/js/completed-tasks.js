// static/js/completed-tasks.js
export async function fetchCompletedTasks(year, month, day) {
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}/completed`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        console.log(`[fetchCompletedTasks] Response status for ${year}-${month}-${day}:`, response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log(`[fetchCompletedTasks] Data for ${year}-${month}-${day}:`, JSON.stringify(data, null, 2));
        if (!data.success || !data.data) {
            console.warn(`[fetchCompletedTasks] Invalid response data for ${year}-${month}-${day}:`, data);
            return [];
        }
        return data.data.completedTasks || [];
    } catch (error) {
        console.error(`[fetchCompletedTasks] Error for ${year}-${month}-${day}:`, error);
        return [];
    }
}