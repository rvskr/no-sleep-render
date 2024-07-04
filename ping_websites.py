from flask import Flask, render_template, request, jsonify
import requests
import time
import subprocess

app = Flask(__name__)

# Структура данных для хранения информации о сайтах
sites_info = [
    {"type": "http", "url": "https://exel-to-gsheets.onrender.com/", "status": None, "last_checked": None, "uptime": 0, "check_interval": 10},
    {"type": "http", "url": "https://your-service-name-v8vp.onrender.com", "status": None, "last_checked": None, "uptime": 0, "check_interval": 10},
    {"type": "http", "url": "https://text-chat.onrender.com", "status": None, "last_checked": None, "uptime": 0, "check_interval": 10}
]

def check_http_site(url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        end_time = time.time()
        response_time = end_time - start_time

        if response.status_code == 200:
            return True, response_time
        else:
            return False, response_time
    except requests.exceptions.RequestException:
        return False, None

def check_ping_site(url):
    try:
        start_time = time.time()
        result = subprocess.run(['ping', '-c', '1', url], capture_output=True, text=True, timeout=10)
        end_time = time.time()
        response_time = end_time - start_time

        if result.returncode == 0:
            return True, response_time
        else:
            return False, response_time
    except subprocess.TimeoutExpired:
        return False, None
    except subprocess.CalledProcessError:
        return False, None

def update_sites_status():
    for site in sites_info:
        if site["type"] == "http":
            status, response_time = check_http_site(site["url"])
        elif site["type"] == "ping":
            status, response_time = check_ping_site(site["url"])
        else:
            status, response_time = False, None
        
        site["status"] = status
        site["last_checked"] = time.strftime('%Y-%m-%d %H:%M:%S')
        if status:
            site["uptime"] += response_time if response_time else 0
        else:
            site["uptime"] = 0

@app.route('/')
def index():
    return render_template('index.html', sites=sites_info)

@app.route('/monitoring')
def monitoring():
    return render_template('index.html', sites=sites_info)

@app.route('/sites', methods=['GET'])
def get_sites():
    return jsonify(sites_info)

@app.route('/sites', methods=['POST'])
def add_site():
    data = request.get_json()
    new_url = data.get('url')
    new_type = data.get('type')
    check_interval = int(data.get('check_interval', 10))  # По умолчанию проверка каждые 10 секунд

    if new_url and new_type and not any(site["url"] == new_url for site in sites_info):
        sites_info.append({
            "type": new_type,
            "url": new_url,
            "status": None,
            "last_checked": None,
            "uptime": 0,
            "check_interval": check_interval
        })
        return jsonify({'message': 'Site added successfully'}), 201
    else:
        return jsonify({'error': 'Site already exists or invalid URL or type'}), 400

@app.route('/sites/<path:url>', methods=['DELETE'])
def delete_site(url):
    for site in sites_info:
        if site["url"] == url:
            sites_info.remove(site)
            return jsonify({'message': 'Site deleted successfully'}), 200
    return jsonify({'error': 'Site not found'}), 404

@app.route('/sites/<path:url>', methods=['PUT'])
def update_site(url):
    data = request.get_json()
    new_type = data.get('type')
    check_interval = int(data.get('check_interval', 10))

    for site in sites_info:
        if site["url"] == url:
            site["type"] = new_type if new_type else site["type"]
            site["check_interval"] = check_interval
            return jsonify({'message': 'Site updated successfully'}), 200
    return jsonify({'error': 'Site not found'}), 404

if __name__ == '__main__':
    def monitor_sites():
        while True:
            update_sites_status()
            time.sleep(10)  # Проверка каждые 10 секунд

    import threading
    monitor_thread = threading.Thread(target=monitor_sites)
    monitor_thread.start()

    app.run(host='0.0.0.0', port=8080, debug=True)  # Замените 8080 на порт, который нужно использовать
