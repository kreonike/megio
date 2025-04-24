// static/js/time.js

export function handleTimeInput(e) {
    this.value = formatTimeInput(this.value);
    this.addEventListener('blur', () => {
        this.value = validateTime(this.value);
    });
}

// Функции для работы с временем
function formatTimeInput(value) {
    let numbers = value.replace(/\D/g, '');
    if (numbers.length > 2) {
        numbers = numbers.substring(0, 4);
        return numbers.substring(0, 2) + ':' + numbers.substring(2, 4);
    }
    return numbers;
}

function validateTime(timeStr) {
    if (!timeStr || typeof timeStr !== 'string') return '12:00';
    let [hours, minutes] = timeStr.includes(':') ? timeStr.split(':') : [timeStr.substring(0, 2), timeStr.substring(2, 4)];
    hours = Math.min(23, Math.max(0, parseInt(hours) || 0));
    minutes = Math.min(59, Math.max(0, parseInt(minutes) || 0));
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

function updateTime(input, change) {
    let time = validateTime(input.value);
    let [hours, minutes] = time.split(':').map(Number);
    minutes += change;
    if (minutes >= 60) {
        minutes = 0;
        hours = (hours + 1) % 24;
    } else if (minutes < 0) {
        minutes = 55;
        hours = (hours - 1 + 24) % 24;
    }
    input.value = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

// Функции для форматирования даты
function formatDateToRussian(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
        const parts = dateStr.split('-');
        if (parts.length === 3) {
            return `${parts[2]}.${parts[1]}.${parts[0]}`;
        }
        return dateStr;
    }
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}.${month}.${year}`;
}

function formatDateForInput(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
        const parts = dateStr.split('.');
        if (parts.length === 3) {
            return `${parts[2]}-${parts[1]}-${parts[0]}`;
        }
        return dateStr;
    }
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Вспомогательная функция для привязки событий спиннера времени
function bindTimeSpinnerEvents(timeInput) {
    timeInput.addEventListener('input', function() { this.value = formatTimeInput(this.value); });
    timeInput.addEventListener('blur', function() { this.value = validateTime(this.value); });
    timeInput.addEventListener('focus', function() { this.select(); });
    timeInput.addEventListener('wheel', function(e) {
        e.preventDefault();
        updateTime(this, e.deltaY > 0 ? -5 : 5);
    });

    const upBtn = timeInput.parentElement.querySelector('.time-btn.up');
    const downBtn = timeInput.parentElement.querySelector('.time-btn.down');
    if (upBtn) upBtn.addEventListener('click', () => updateTime(timeInput, 5));
    if (downBtn) downBtn.addEventListener('click', () => updateTime(timeInput, -5));
}

// Экспорт функций для использования в других файлах
export {
    formatTimeInput,
    validateTime,
    updateTime,
    formatDateToRussian,
    formatDateForInput,
    bindTimeSpinnerEvents
};