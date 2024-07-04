from flask import Flask
import os
from dotenv import load_dotenv
import schedule
import time
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

app = Flask(__name__)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Считываем список URL сайтов из переменной окружения
site_urls_str = os.getenv('SITE_URLS')
if site_urls_str:
    site_urls = [url.strip() for url in site_urls_str.split(',')]
    print(f'Loaded SITE_URLS: {site_urls}')
else:
    print('Variable SITE_URLS is not set or empty. Please check your environment setup.')
    exit()

# Функция для имитации доступа пользователя к сайту
def try_access_website(url):
    try:
        # Используем Selenium для имитации открытия браузера и загрузки страницы
        options = webdriver.ChromeOptions()
        options.add_argument('headless')  # Запуск браузера в фоновом режиме (без GUI)
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        print(f'Successfully tried to access {url}')
    except Exception as e:
        print(f'Error trying to access {url}: {str(e)}')
    finally:
        if driver:
            driver.quit()

# Функция для имитации доступа к сайтам в списке
def schedule_access():
    for url in site_urls:
        try_access_website(url)
    
    # Задаем случайный интервал в секундах от 60 до 180 (1 минута до 3 минут)
    random_interval = random.randint(10, 100)
    print(f'Next access attempt in {random_interval} seconds')

    # Запускаем расписание для следующей попытки доступа через случайное время
    schedule.every(random_interval).seconds.do(schedule_access)

@app.route('/')
def index():
    return 'Hello, World!'

if __name__ == '__main__':
    # Начальная имитация доступа к сайтам
    schedule_access()

    # Бесконечный цикл для выполнения расписания
    while True:
        schedule.run_pending()
        time.sleep(1)
