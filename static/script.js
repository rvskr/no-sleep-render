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
                this.textContent = this.getAttribute('data-interval');
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
            enabled: true
        })
    }).then(response => {
        if (!response.ok) {
            alert('Ошибка обновления интервала.');
        }
    });
}

function toggleMonitoring(url, currentState) {
    fetch('/toggle_monitoring', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            url: url,
            enabled: !currentState
        })
    }).then(response => {
        if (response.ok) {
            location.reload();
        } else {
            alert('Ошибка изменения состояния мониторинга.');
        }
    });
}

function showAddSiteModal() {
    document.getElementById('addSiteModal').style.display = 'block';
}

function hideAddSiteModal() {
    document.getElementById('addSiteModal').style.display = 'none';
}
