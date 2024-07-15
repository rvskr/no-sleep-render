import os
import requests
import threading
import logging
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import time

# Загрузка переменных окружения из .env файла
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Конфигурация Supabase из переменных окружения
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Глобальные переменные для хранения статуса сайта
site_status = {}
site_last_checked = {}
monitor_threads = {}
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
def monitor_site(url, flag):
    global site_status, site_last_checked
    while not flag.is_set():
        # Получаем интервал из базы данных
        site = supabase.table('sites').select('interval').eq('url', url).execute()
        if site.data:
            interval = site.data[0]['interval']
        else:
            logging.error(f"Не удалось найти интервал для {url} в базе данных.")
            break

        status = check_http_site(url)
        site_status[url] = 'UP' if status else 'DOWN'
        site_last_checked[url] = datetime.now(timezone.utc)
        logging.info(f"Статус сайта {url}: {'UP' if status else 'DOWN'}")
        logging.info(f"Следующая проверка сайта {url} через {interval} секунд.")
        flag.wait(interval)

# Функция для периодической проверки всех сайтов из базы данных
def periodic_check():
    while True:
        sites = supabase.table('sites').select('*').execute().data
        for site in sites:
            url = site['url']
            interval = site['interval']
            if url not in monitor_threads or not monitor_threads[url].is_alive():
                flag = threading.Event()
                thread = threading.Thread(target=monitor_site, args=(url, flag))
                monitor_threads[url] = thread
                monitor_flags[url] = flag
                thread.start()
        time.sleep(300)  # Ожидание 5 минут

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        interval = int(request.form['interval'])

        if 'authenticated' not in session:
            flash('Пожалуйста, введите пароль для выполнения этой операции.', 'error')
            return redirect(url_for('login'))

        # Запуск мониторинга в отдельном потоке для каждого сайта
        if url not in monitor_threads or not monitor_threads[url].is_alive():
            flag = threading.Event()
            thread = threading.Thread(target=monitor_site, args=(url, flag))
            monitor_threads[url] = thread
            monitor_flags[url] = flag
            thread.start()
            logging.info(f"Запущен мониторинг сайта {url} с интервалом {interval} секунд.")

            # Сохранение данных в Supabase
            data = {"url": url, "interval": interval}
            supabase.table('sites').insert(data).execute()

        return redirect(url_for('index'))

    # Получение списка сайтов из Supabase
    sites = supabase.table('sites').select('*').execute().data
    site_details = [{'url': site['url'], 'status': site_status.get(site['url'], 'UNKNOWN'), 'last_checked': site_last_checked.get(site['url'], 'Never'), 'interval': site['interval']} for site in sites]
    return render_template('index.html', sites=site_details)

@app.route('/delete', methods=['POST'])
def delete_site():
    url = request.form['url']

    if 'authenticated' not in session:
        flash('Пожалуйста, введите пароль для выполнения этой операции.', 'error')
        return redirect(url_for('login'))

    if url in monitor_threads:
        monitor_flags[url].set()  # Установить флаг для завершения потока
        monitor_threads[url].join()  # Дождаться завершения потока
        del monitor_threads[url]
        del site_status[url]
        del site_last_checked[url]
        del monitor_flags[url]
        logging.info(f"Мониторинг сайта {url} остановлен и сайт удален.")

        # Удаление данных из Supabase
        supabase.table('sites').delete().eq('url', url).execute()
    return redirect(url_for('index'))

def update_site_in_db(url, new_interval):
    """Обновляет интервал для сайта в Supabase."""
    supabase.table('sites').update({'interval': new_interval}).eq('url', url).execute()

@app.route('/update', methods=['POST'])
def update_site():
    data = request.json
    url = data.get('url')
    new_interval = data.get('interval')

    if url and new_interval:
        # Обновляем интервал в базе данных
        update_site_in_db(url, new_interval)
        
        # Остановка текущего потока мониторинга
        if url in monitor_threads:
            monitor_flags[url].set()  # Устанавливаем флаг для остановки
            monitor_threads[url].join()  # Ждем завершения потока
        
        # Запуск нового потока с обновленным интервалом
        flag = threading.Event()
        thread = threading.Thread(target=monitor_site, args=(url, flag))
        monitor_threads[url] = thread
        monitor_flags[url] = flag
        thread.start()

        app.logger.info(f"Интервал мониторинга сайта {url} обновлен до {new_interval} секунд.")
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="Некорректные данные."), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            flash('Аутентификация успешна!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный пароль!', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Запуск периодической проверки в отдельном потоке
    threading.Thread(target=periodic_check, daemon=True).start()
    app.run(debug=True)