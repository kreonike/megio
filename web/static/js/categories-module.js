export function initCategories() {
    console.log('[categories-module] Initializing category form handler');

    // Обработчик для формы добавления категории
    const categoryForm = document.getElementById('category-form');
    if (categoryForm) {
        categoryForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            console.log('[categories-module] Category form submitted');

            const formData = new FormData(categoryForm);
            try {
                const response = await fetch('/profile', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                // Логируем статус и содержимое ответа
                console.log('[categories-module] Response status:', response.status);
                const responseText = await response.text();
                console.log('[categories-module] Response text:', responseText);

                // Пытаемся разобрать JSON
                let data;
                try {
                    data = JSON.parse(responseText);
                } catch (e) {
                    console.error('[categories-module] JSON parse error:', e, 'Response:', responseText);
                    showFlashMessage('Ошибка: сервер вернул некорректный ответ', 'error');
                    return;
                }

                console.log('[categories-module] Server response:', data);

                if (data.success) {
                    // Добавляем новую категорию в список
                    addCategoryToList(data.category);
                    showFlashMessage(data.message, 'success');
                    // Очищаем форму
                    categoryForm.reset();
                    categoryForm.querySelector('input[name="color"]').value = '#3498db';
                } else {
                    showFlashMessage(data.message || 'Ошибка добавления категории', 'error');
                }
            } catch (error) {
                console.error('[categories-module] Fetch error:', error);
                showFlashMessage('Ошибка связи с сервером', 'error');
            }
        });
    }

    // Обработчик для форм удаления категорий
    const deleteForms = document.querySelectorAll('.delete-category-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            console.log('[categories-module] Delete category form submitted');

            const formData = new FormData(form);
            try {
                const response = await fetch('/profile', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const responseText = await response.text();
                console.log('[categories-module] Delete response text:', responseText);

                let data;
                try {
                    data = JSON.parse(responseText);
                } catch (e) {
                    console.error('[categories-module] Delete JSON parse error:', e, 'Response:', responseText);
                    showFlashMessage('Ошибка: сервер вернул некорректный ответ', 'error');
                    return;
                }

                console.log('[categories-module] Delete response:', data);

                if (data.success) {
                    removeCategoryFromList(data.category_id);
                    showFlashMessage(data.message, 'success');
                } else {
                    showFlashMessage(data.message || 'Ошибка удаления категории', 'error');
                }
            } catch (error) {
                console.error('[categories-module] Delete fetch error:', error);
                showFlashMessage('Ошибка связи с сервером', 'error');
            }
        });
    });
}

// Функция для добавления категории в список
function addCategoryToList(category) {
    const categoriesList = document.querySelector('.categories-list');
    let categoryGrid = document.querySelector('.category-grid');

    if (!categoryGrid) {
        categoriesList.innerHTML = '<div class="category-grid"></div>';
        categoryGrid = categoriesList.querySelector('.category-grid');
        const noCategories = categoriesList.querySelector('.no-categories');
        if (noCategories) {
            noCategories.remove();
        }
    }

    const categoryItem = document.createElement('div');
    categoryItem.className = 'category-item';
    categoryItem.dataset.categoryId = category.id;
    categoryItem.innerHTML = `
        <span class="category-badge" style="background-color: ${category.color}">${category.name}</span>
        <form method="POST" class="delete-category-form" style="margin: 0;">
            <input type="hidden" name="delete_category" value="${category.id}">
            <button type="submit" class="btn btn-danger btn-sm">
                <i class="fas fa-trash-alt"></i>
            </button>
        </form>
    `;

    categoryGrid.appendChild(categoryItem);

    const deleteForm = categoryItem.querySelector('.delete-category-form');
    deleteForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(deleteForm);
        try {
            const response = await fetch('/profile', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const responseText = await response.text();
            let data;
            try {
                data = JSON.parse(responseText);
            } catch (e) {
                console.error('[categories-module] Delete JSON parse error:', e, 'Response:', responseText);
                showFlashMessage('Ошибка: сервер вернул некорректный ответ', 'error');
                return;
            }

            if (data.success) {
                removeCategoryFromList(data.category_id);
                showFlashMessage(data.message, 'success');
            } else {
                showFlashMessage(data.message || 'Ошибка удаления категории', 'error');
            }
        } catch (error) {
            console.error('[categories-module] Delete fetch error:', error);
            showFlashMessage('Ошибка связи с сервером', 'error');
        }
    });

    // Обновляем календарь после добавления категории
    const calendarTable = document.querySelector('.calendar-table');
    if (calendarTable) {
        const year = parseInt(calendarTable.dataset.year);
        const month = parseInt(calendarTable.dataset.month);
        import('./calendar-module.js').then(({ updateCalendar }) => {
            updateCalendar(year, month).then(() => {
                console.log('[categories-module] Calendar updated after adding category');
            });
        });
    }
}

// Функция для удаления категории из списка
function removeCategoryFromList(categoryId) {
    const categoryItem = document.querySelector(`.category-item[data-category-id="${categoryId}"]`);
    if (categoryItem) {
        categoryItem.remove();
    }

    const categoryGrid = document.querySelector('.category-grid');
    if (categoryGrid && categoryGrid.children.length === 0) {
        const categoriesList = document.querySelector('.categories-list');
        categoriesList.innerHTML = '<p class="no-categories">Нет созданных категорий</p>';
    }

    // Обновляем календарь после удаления категории
    const calendarTable = document.querySelector('.calendar-table');
    if (calendarTable) {
        const year = parseInt(calendarTable.dataset.year);
        const month = parseInt(calendarTable.dataset.month);
        import('./calendar-module.js').then(({ updateCalendar }) => {
            updateCalendar(year, month).then(() => {
                console.log('[categories-module] Calendar updated after removing category');
            });
        });
    }
}

// Функция для показа flash-сообщений
function showFlashMessage(message, category) {
    const flashContainer = document.querySelector('.flash-messages') || document.createElement('div');
    if (!flashContainer.classList.contains('flash-messages')) {
        flashContainer.className = 'flash-messages';
        document.querySelector('.profile-container').prepend(flashContainer);
    }

    const flashDiv = document.createElement('div');
    flashDiv.className = `flash ${category}`;
    flashDiv.textContent = message;
    flashContainer.appendChild(flashDiv);

    setTimeout(() => {
        flashDiv.remove();
    }, 5000);
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    initCategories();
});