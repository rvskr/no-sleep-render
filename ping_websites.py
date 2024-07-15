import requests
import threading
import time
import logging
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Глобальные переменные для хранения статуса сайта
site_status = {}
site_last_checked = {}
monitor_threads = {}
monitor_intervals = {}
monitor_flags = {}

# Функция для проверки статуса сайта
def check_http_site(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при проверке {url}: {e}")
        return False

# Функция мониторинга сайта
def monitor_site(url, interval, flag):
    global site_status, site_last_checked
    while not flag.is_set():
        status = check_http_site(url)
        site_status[url] = 'UP' if status else 'DOWN'
        site_last_checked[url] = datetime.now(timezone.utc)
        logging.info(f"Статус сайта {url}: {'UP' if status else 'DOWN'}")
        logging.info(f"Следующая проверка сайта {url} через {interval} секунд.")
        flag.wait(interval)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        interval = int(request.form['interval'])

        # Запуск мониторинга в отдельном потоке для каждого сайта
        if url not in monitor_threads or not monitor_threads[url].is_alive():
            flag = threading.Event()
            thread = threading.Thread(target=monitor_site, args=(url, interval, flag))
            monitor_threads[url] = thread
            monitor_intervals[url] = interval
            monitor_flags[url] = flag
            thread.start()
            logging.info(f"Запущен мониторинг сайта {url} с интервалом {interval} секунд.")
        else:
            logging.info(f"Сайт {url} уже отслеживается.")

        return redirect(url_for('index'))

    # Список сайтов для отображения на странице
    sites = [{'url': url, 'status': site_status.get(url, 'UNKNOWN'), 'last_checked': site_last_checked.get(url, 'Never'), 'interval': monitor_intervals.get(url, 'N/A')} for url in monitor_threads.keys()]
    return render_template('index.html', sites=sites)

@app.route('/delete', methods=['POST'])
def delete_site():
    url = request.form['url']
    if url in monitor_threads:
        monitor_flags[url].set()  # Установить флаг для завершения потока
        monitor_threads[url].join()  # Дождаться завершения потока
        del monitor_threads[url]
        del site_status[url]
        del site_last_checked[url]
        del monitor_intervals[url]
        del monitor_flags[url]
        logging.info(f"Мониторинг сайта {url} остановлен и сайт удален.")
    return redirect(url_for('index'))

@app.route('/update', methods=['POST'])
def update_site():
    url = request.form['url']
    interval = int(request.form['interval'])
    if url in monitor_threads:
        monitor_flags[url].set()  # Установить флаг для завершения текущего потока
        monitor_threads[url].join()  # Дождаться завершения текущего потока
        monitor_flags[url] = threading.Event()  # Создать новый флаг для нового потока
        thread = threading.Thread(target=monitor_site, args=(url, interval, monitor_flags[url]))
        monitor_threads[url] = thread
        monitor_intervals[url] = interval
        thread.start()
        logging.info(f"Интервал мониторинга сайта {url} обновлен до {interval} секунд.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
