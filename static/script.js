document.addEventListener('DOMContentLoaded', () => {
    const intervalCells = document.querySelectorAll('.interval-cell');

    intervalCells.forEach(cell => {
        cell.addEventListener('blur', function () {
            const url = this.getAttribute('data-url');
            const newInterval = this.textContent;

            if (!isNaN(newInterval) && newInterval > 0) {
                updateInterval(url, newInterval);
            } else {
                alert('Интервал должен быть числом больше нуля.');
                this.textContent = this.getAttribute('data-interval');  // Вернуть старое значение
            }
        });

        cell.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.blur();
            }
        });
    });
});

function updateInterval(url, newInterval) {
    fetch('/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            url: url,
            interval: newInterval,
        })
    }).then(response => {
        if (response.ok) {
            const cell = document.querySelector(`.interval-cell[data-url="${url}"]`);
            if (cell) {
                cell.setAttribute('data-interval', newInterval);
            }
        } else {
            alert('Ошибка обновления интервала.');
        }
    }).catch(error => {
        console.error('Ошибка:', error);
    });
}

function toggleMonitoring(url, isEnabled) {
    fetch('/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url, enabled: !isEnabled }),  // Переключаем статус
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();  // Обновление страницы для обновления статуса сайтов
        } else {
            alert(data.message);
        }
    })
    .catch(error => console.error('Ошибка:', error));
}

function showAddSiteModal() {
    document.getElementById('addSiteModal').style.display = 'block';
}

function hideAddSiteModal() {
    document.getElementById('addSiteModal').style.display = 'none';
}

function deleteSite(url) {
    fetch('/delete_site', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();  // Обновление страницы для обновления списка сайтов
        } else {
            alert(data.message);
        }
    })
    .catch(error => console.error('Ошибка:', error));
}
