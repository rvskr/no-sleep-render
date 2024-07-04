import os
import requests
from dotenv import load_dotenv
import schedule
import time

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

def ping_website(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f'Successfully pinged {url}')
        else:
            print(f'Failed to ping {url}. Status code: {response.status_code}')
    except Exception as e:
        print(f'Error pinging {url}: {str(e)}')

def schedule_ping():
    for url in site_urls:
        ping_website(url)

# Назначаем задачу пинга каждые 3 минуты
schedule.every(1).minutes.do(schedule_ping)

if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(1)
