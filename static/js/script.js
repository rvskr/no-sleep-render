function editInterval(cell) {
    const currentInterval = cell.innerText;
    const newInterval = prompt("Введите новый интервал (в секундах):", currentInterval);
    
    if (newInterval !== null && !isNaN(newInterval)) {
        const url = cell.getAttribute('data-url');

        fetch('/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url, interval: parseInt(newInterval) })
        })
        .then(response => {
            if (response.ok) {
                cell.innerText = newInterval;
                alert("Интервал обновлен!");
            } else {
                alert("Ошибка обновления интервала.");
            }
        })
        .catch(error => {
            console.error("Ошибка:", error);
            alert("Ошибка при связи с сервером.");
        });
    }
}
