import os
import requests
import threading
import logging
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import time
import asyncio
import aiohttp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

site_status = {}
site_last_checked = {}
monitor_threads = {}
monitor_flags = {}
site_cache = {}

def log_function_call(func, *args, **kwargs):
    logging.info(f"Вызов функции {func.__name__} с аргументами {args} и ключевыми аргументами {kwargs}")
    return func

async def check_http_site_async(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logging.error(f"Ошибка при проверке {url}: {e}")
            return False

def monitor_site(url, flag):
    log_function_call(monitor_site, url, flag)
    global site_status, site_last_checked, site_cache
    while not flag.is_set():
        site_info = site_cache.get(url, None)
        if site_info:
            interval = site_info.get('interval')
        else:
            logging.error(f"Не удалось найти интервал для {url} в кэше.")
            break

        start_time = time.time()
        status = asyncio.run(check_http_site_async(url))
        site_status[url] = 'UP' if status else 'DOWN'
        site_last_checked[url] = datetime.now(timezone.utc)
        end_time = time.time()
        logging.info(f"Статус сайта {url}: {'UP' if status else 'DOWN'}")
        logging.info(f"Проверка заняла {end_time - start_time:.2f} секунд.")
        
        time_taken = end_time - start_time
        time_to_wait = max(0, interval - time_taken)
        logging.info(f"Следующая проверка сайта {url} через {time_to_wait:.2f} секунд.")
        flag.wait(time_to_wait)

def update_cache():
    global site_cache
    try:
        sites = supabase.table('sites').select('url', 'interval', 'enabled').execute().data
        site_cache = {site['url']: site for site in sites}
        logging.info("Кэш обновлен. Данные сайтов: %s", site_cache)
    except Exception as e:
        logging.error(f"Ошибка обновления кэша: {e}")

def initialize_monitors():
    global monitor_threads, monitor_flags
    for url, site_info in site_cache.items():
        if site_info['enabled']:
            if url not in monitor_threads or not monitor_threads[url].is_alive():
                flag = threading.Event()
                thread = threading.Thread(target=monitor_site, args=(url, flag))
                monitor_threads[url] = thread
                monitor_flags[url] = flag
                thread.start()
                logging.info(f"Запущен мониторинг сайта {url} с интервалом {site_info['interval']} секунд.")
        else:
            if url in monitor_threads and monitor_threads[url].is_alive():
                monitor_flags[url].set()
                monitor_threads[url].join()
                del monitor_threads[url]
                del monitor_flags[url]
                logging.info(f"Мониторинг сайта {url} остановлен.")

@app.route('/', methods=['GET', 'POST'])
def index():
    log_function_call(index)
    if request.method == 'POST':
        return handle_post()
    return render_index()

def handle_post():
    log_function_call(handle_post)
    url = request.form['url']
    interval = int(request.form['interval'])
    enabled = 'enabled' in request.form

    if 'authenticated' not in session:
        flash('Пожалуйста, введите пароль для выполнения этой операции.', 'error')
        return redirect(url_for('login'))

    data = {"url": url, "interval": interval, "enabled": enabled}
    supabase.table('sites').insert(data).execute()
    update_cache()

    if enabled:
        flag = threading.Event()
        thread = threading.Thread(target=monitor_site, args=(url, flag))
        monitor_threads[url] = thread
        monitor_flags[url] = flag
        thread.start()
        logging.info(f"Запущен мониторинг сайта {url} с интервалом {interval} секунд.")

    return redirect(url_for('index'))

def render_index():
    log_function_call(render_index)
    sites = list(site_cache.values())
    site_details = [{'url': site['url'],
                     'status': site_status.get(site['url'], 'NOT MONITORED'),
                     'last_checked': site_last_checked.get(site['url'], 'Never'),
                     'interval': site['interval'],
                     'enabled': site['enabled']} for site in sites]
    return render_template('index.html', sites=site_details)

@app.route('/update', methods=['POST'])
def update_site():
    log_function_call(update_site)
    data = request.json
    url = data.get('url')
    new_interval = data.get('interval')
    enabled = data.get('enabled')

    update_data = {}
    if new_interval is not None:
        update_data['interval'] = new_interval
    if enabled is not None:
        update_data['enabled'] = enabled

    if update_data:
        try:
            supabase.table('sites').update(update_data).eq('url', url).execute()
            update_cache()
            logging.info(f"Обновлены данные для {url}: {update_data}")

            if 'enabled' in update_data:
                if update_data['enabled']:
                    if url not in monitor_threads or not monitor_threads[url].is_alive():
                        flag = threading.Event()
                        thread = threading.Thread(target=monitor_site, args=(url, flag))
                        monitor_threads[url] = thread
                        monitor_flags[url] = flag
                        thread.start()
                        logging.info(f"Мониторинг сайта {url} запущен.")
                else:
                    if url in monitor_threads and monitor_threads[url].is_alive():
                        monitor_flags[url].set()
                        monitor_threads[url].join()
                        del monitor_threads[url]
                        del monitor_flags[url]
                    site_status[url] = 'NOT MONITORED'
                    logging.info(f"Мониторинг сайта {url} остановлен.")

            return jsonify(success=True)
        except Exception as e:
            logging.error(f"Ошибка обновления {url}: {e}")
            return jsonify(success=False, message=str(e)), 400

    return jsonify(success=False, message="Некорректные данные."), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    log_function_call(login)
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['authenticated'] = True
            flash('Аутентификация успешна!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный пароль!', 'error')
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    log_function_call(logout)
    session.pop('authenticated', None)
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('login'))

@app.route('/delete_site', methods=['POST'])
def delete_site():
    log_function_call(delete_site)
    url = request.json.get('url')
    
    try:
        response = supabase.table('sites').delete().eq('url', url).execute()
        if response.data:
            logging.info(f"Сайт {url} успешно удалён.")
            if url in monitor_threads and monitor_threads[url].is_alive():
                monitor_flags[url].set()
                monitor_threads[url].join()
                del monitor_threads[url]
                del monitor_flags[url]
            site_status[url] = 'NOT MONITORED'
            update_cache()
            return jsonify({'success': True})
        else:
            logging.error(f"Не удалось удалить сайт {url}, возможно, он не найден.")
            return jsonify({'success': False, 'message': 'Сайт не найден.'}), 404
    except Exception as e:
        logging.error(f"Ошибка при удалении сайта {url}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def periodic_monitoring():
    while True:
        try:
            update_cache()
            for site in site_cache.values():
                if site['enabled']:
                    status = asyncio.run(check_http_site_async(site['url']))
                    site_status[site['url']] = 'UP' if status else 'DOWN'
                    site_last_checked[site['url']] = datetime.now(timezone.utc)
            time.sleep(60)  # Период обновления в 60 секунд
        except Exception as e:
            logging.error(f"Ошибка при периодическом мониторинге: {e}")

if __name__ == '__main__':
    update_cache()
    initialize_monitors()  # Запуск мониторинга для сайтов из базы данных
    monitoring_thread = threading.Thread(target=periodic_monitoring)
    monitoring_thread.start()
    app.run(debug=False)
