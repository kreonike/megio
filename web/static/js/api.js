// static/js/api.js
export async function fetchTasks(year, month, day) {
    /**
     * Запрашивает задачи для указанного дня.
     *
     * @param {number} year - Год.
     * @param {number} month - Месяц.
     * @param {number} day - День.
     * @returns {Object} Данные ответа сервера.
     */
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        console.log(`[api/fetchTasks] Статус ответа для ${year}-${month}-${day}:`, response.status);
        if (!response.ok) throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        const data = await response.json();
        if (!data.success || !data.data) {
            console.warn(`[api/fetchTasks] Некорректные данные ответа для ${year}-${month}-${day}:`, data);
            return { success: false, data: null };
        }
        return data;
    } catch (error) {
        console.error(`[api/fetchTasks] Ошибка для ${year}-${month}-${day}:`, error);
        return { success: false, data: null };
    }
}

export async function fetchMonthTasks(year, month) {
    /**
     * Запрашивает задачи за месяц.
     *
     * @param {number} year - Год.
     * @param {number} month - Месяц.
     * @returns {Object} Данные ответа сервера.
     */
    try {
        const response = await fetch(`/tasks/${year}/${month}`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        console.log(`[api/fetchMonthTasks] Статус ответа для ${year}-${month}:`, response.status);
        if (!response.ok) throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        const data = await response.json();
        console.log(`[api/fetchMonthTasks] Данные для ${year}-${month}:`, data);
        if (!data.success || !data.data) {
            console.warn(`[api/fetchMonthTasks] Некорректные данные ответа для ${year}-${month}:`, data);
            return { success: false, data: null };
        }
        return data;
    } catch (error) {
        console.error(`[api/fetchMonthTasks] Ошибка для ${year}-${month}:`, error);
        return { success: false, data: null };
    }
}

export async function fetchCompletedTasks(year, month, day) {
    /**
     * Запрашивает завершённые задачи для указанного дня.
     *
     * @param {number} year - Год.
     * @param {number} month - Месяц.
     * @param {number} day - День.
     * @returns {Array} Список завершённых задач.
     */
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}/completed`, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        console.log(`[api/fetchCompletedTasks] Статус ответа для ${year}-${month}-${day}:`, response.status);
        if (!response.ok) throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        const data = await response.json();
        console.log(`[api/fetchCompletedTasks] Данные для ${year}-${month}-${day}:`, JSON.stringify(data, null, 2));
        if (!data.success || !data.data) {
            console.warn(`[api/fetchCompletedTasks] Некорректные данные ответа для ${year}-${month}-${day}:`, data);
            return [];
        }
        const completedTasks = data.data.completedTasks || [];
        return completedTasks;
    } catch (error) {
        console.error(`[api/fetchCompletedTasks] Ошибка для ${year}-${month}-${day}:`, error);
        return [];
    }
}

export async function restoreTask(year, month, day, taskId) {
    /**
     * Восстанавливает завершённую задачу.
     *
     * @param {number} year - Год.
     * @param {number} month - Месяц.
     * @param {number} day - День.
     * @param {number} taskId - ID задачи.
     * @returns {Object} Данные ответа сервера.
     */
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
            throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`[api/restoreTask] Ошибка для задачи ${taskId}:`, error);
        throw error;
    }
}

export async function completeTask(year, month, day, taskId) {
    /**
     * Помечает задачу как завершённую.
     *
     * @param {number} year - Год.
     * @param {number} month - Месяц.
     * @param {number} day - День.
     * @param {number} taskId - ID задачи.
     * @returns {Object} Данные ответа сервера.
     */
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ task_id: taskId })
        });
        if (!response.ok) throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`[api/completeTask] Ошибка для задачи ${taskId}:`, error);
        throw error;
    }
}

export async function deleteTask(year, month, day, taskId) {
    /**
     * Удаляет задачу.
     *
     * @param {number} year - Год.
     * @param {number} month - Месяц.
     * @param {number} day - День.
     * @param {number} taskId - ID задачи.
     * @returns {Object} Данные ответа сервера.
     */
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `delete=${taskId}`
        });
        if (!response.ok) throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`[api/deleteTask] Ошибка для задачи ${taskId}:`, error);
        throw error;
    }
}

export async function setReminders(year, month, day, taskId, remindTimes) {
    /**
     * Устанавливает напоминания для задачи.
     *
     * @param {number} year - Год.
     * @param {number} month - Месяц.
     * @param {number} day - День.
     * @param {number} taskId - ID задачи.
     * @param {Array} remindTimes - Времена напоминаний.
     * @returns {Object} Данные ответа сервера.
     */
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}/remind`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ task_id: taskId, remind_times: remindTimes })
        });
        if (!response.ok) throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`[api/setReminders] Ошибка для задачи ${taskId}:`, error);
        throw error;
    }
}

export async function createTask(year, month, day, formData) {
    /**
     * Создаёт новую задачу.
     *
     * @param {number} year - Год.
     * @param {number} month - Месяц.
     * @param {number} day - День.
     * @param {FormData} formData - Данные формы.
     * @returns {Object} Данные ответа сервера.
     */
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        });
        if (!response.ok) throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`[api/createTask] Ошибка:`, error);
        throw error;
    }
}

export async function updateTask(year, month, day, formData) {
    /**
     * Обновляет существующую задачу.
     *
     * @param {number} year - Год.
     * @param {number} month - Месяц.
     * @param {number} day - День.
     * @param {FormData} formData - Данные формы.
     * @returns {Object} Данные ответа сервера.
     */
    try {
        const response = await fetch(`/tasks/${year}/${month}/${day}`, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        });
        if (!response.ok) throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`[api/updateTask] Ошибка:`, error);
        throw error;
    }
}