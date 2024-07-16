document.addEventListener('DOMContentLoaded', () => {
    const intervalCells = document.querySelectorAll('.interval-cell');

    intervalCells.forEach(cell => {
        cell.addEventListener('blur', () => {
            updateInterval(cell);
        });

        cell.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault(); // Предотвращаем добавление новой строки
                updateInterval(cell);
                cell.blur(); // Убираем фокус
            }
        });
    });
});

function updateInterval(cell) {
    const newInterval = cell.textContent.trim();
    const url = cell.dataset.url;

    if (!isNaN(newInterval) && newInterval > 0) {
        fetch('/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: url,
                interval: parseInt(newInterval, 10)
            })
        }).then(response => response.json()).then(data => {
            if (data.success) {
                location.reload(); // Перезагрузить страницу для обновления статусов
            } else {
                alert(data.message);
            }
        });
    } else {
        alert('Некорректный интервал. Пожалуйста, введите положительное число.');
        cell.textContent = cell.dataset.interval; // Возвращаем старое значение
    }
}

function toggleMonitoring(url, enabled) {
    fetch('/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            url: url,
            enabled: !enabled
        })
    }).then(response => response.json()).then(data => {
        if (data.success) {
            location.reload(); // Перезагрузить страницу для обновления статусов
        } else {
            alert(data.message);
        }
    });
}
