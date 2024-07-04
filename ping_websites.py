from flask import Flask
import os
import requests
from dotenv import load_dotenv

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

def ping_website(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f'Successfully pinged {url}')
        else:
            print(f'Failed to ping {url}. Status code: {response.status_code}')
    except Exception as e:
        print(f'Error pinging {url}: {str(e)}')

@app.route('/')
def index():
    return 'Hello, World!'

def schedule_ping():
    for url in site_urls:
        ping_website(url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
