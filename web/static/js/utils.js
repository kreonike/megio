export function formatTimeInput(value) {
    console.log('[utils/formatTimeInput] Formatting input:', value);
    let numbers = value.replace(/\D/g, '');
    if (numbers.length > 2) {
        numbers = numbers.substring(0, 4);
        return numbers.substring(0, 2) + ':' + numbers.substring(2, 4);
    }
    return numbers;
}

export function validateTime(timeStr) {
    console.log('[utils/validateTime] Validating time:', timeStr);
    if (!timeStr || typeof timeStr !== 'string') return '12:00';
    let [hours, minutes] = timeStr.includes(':') ? timeStr.split(':') : [timeStr.substring(0, 2), timeStr.substring(2, 4)];
    hours = Math.min(23, Math.max(0, parseInt(hours) || 0));
    minutes = Math.min(59, Math.max(0, parseInt(minutes) || 0));
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

export function updateTime(input, change) {
    console.log('[utils/updateTime] Updating time for input:', input.value, 'Change:', change);
    let time = validateTime(input.value);
    let [hours, minutes] = time.split(':').map(Number);
    minutes += change;
    if (minutes >= 60) {
        minutes -= 60;
        hours = (hours + 1) % 24;
    } else if (minutes < 0) {
        minutes += 60;
        hours = (hours - 1 + 24) % 24;
    }
    input.value = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

export function formatDateToRussian(dateStr) {
    console.log('[utils/formatDateToRussian] Formatting date:', dateStr);
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

export function formatDateForInput(dateStr) {
    console.log('[utils/formatDateForInput] Formatting date for input:', dateStr);
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

export function formatCompletionTime(timestamp) {
    console.log('[utils/formatCompletionTime] Formatting timestamp:', timestamp);
    try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
        console.warn('[utils/formatCompletionTime] Invalid timestamp:', timestamp);
        return '';
    }
}

export function bindTimeSpinnerEvents(timeInput) {
    console.log('[utils/bindTimeSpinnerEvents] Binding events for input:', timeInput);
    if (!timeInput) {
        console.error('[utils/bindTimeSpinnerEvents] Time input not provided');
        return;
    }

    // Удаляем старые обработчики, чтобы избежать дублирования
    timeInput.removeEventListener('input', handleInput);
    timeInput.removeEventListener('blur', handleBlur);
    timeInput.removeEventListener('focus', handleFocus);
    timeInput.removeEventListener('wheel', handleWheel);

    // Привязываем новые обработчики
    timeInput.addEventListener('input', handleInput);
    timeInput.addEventListener('blur', handleBlur);
    timeInput.addEventListener('focus', handleFocus);
    timeInput.addEventListener('wheel', handleWheel);

    function handleInput() {
        this.value = formatTimeInput(this.value);
    }

    function handleBlur() {
        this.value = validateTime(this.value);
    }

    function handleFocus() {
        this.select();
    }

    function handleWheel(e) {
        e.preventDefault();
        updateTime(this, e.deltaY > 0 ? -5 : 5);
    }

    // Привязка кнопок спиннера
    const timeSelector = timeInput.closest('.time-selector');
    if (!timeSelector) {
        console.warn('[utils/bindTimeSpinnerEvents] Time selector not found for input:', timeInput);
        return;
    }

    const upBtn = timeSelector.querySelector('.time-btn.up');
    const downBtn = timeSelector.querySelector('.time-btn.down');

    if (!upBtn || !downBtn) {
        console.warn('[utils/bindTimeSpinnerEvents] Spinner buttons not found for input:', timeInput);
        return;
    }

    // Удаляем старые обработчики с кнопок
    upBtn.removeEventListener('click', handleUpClick);
    downBtn.removeEventListener('click', handleDownClick);

    // Привязываем новые обработчики
    upBtn.addEventListener('click', handleUpClick);
    downBtn.addEventListener('click', handleDownClick);

    function handleUpClick() {
        updateTime(timeInput, 5);
    }

    function handleDownClick() {
        updateTime(timeInput, -5);
    }
}