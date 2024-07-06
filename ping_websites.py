from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import subprocess
import threading
import time
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sites.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking
db = SQLAlchemy(app)

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)
    url = db.Column(db.String(200), nullable=False, unique=True)
    status = db.Column(db.Boolean)
    last_checked = db.Column(db.DateTime)
    uptime = db.Column(db.Float)
    check_interval = db.Column(db.Integer, default=10)

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
    with app.app_context():
        sites = Site.query.all()

        for site in sites:
            if site.type == "http":
                status, response_time = check_http_site(site.url)
            elif site.type == "ping":
                status, response_time = check_ping_site(site.url)
            else:
                status, response_time = False, None
            
            site.status = status
            site.last_checked = datetime.utcnow()
            if status:
                site.uptime += response_time if response_time else 0
            else:
                site.uptime = 0

        db.session.commit()

@app.route('/')
def index():
    sites = Site.query.all()
    return render_template('index.html', sites=sites)

@app.route('/monitoring')
def monitoring():
    sites = Site.query.all()
    return render_template('index.html', sites=sites)

@app.route('/sites', methods=['GET'])
def get_sites():
    sites = Site.query.all()
    serialized_sites = []
    
    for site in sites:
        serialized_site = {
            'id': site.id,
            'url': site.url,
            'type': site.type,
            'status': site.status,
            'last_checked': site.last_checked.strftime('%Y-%m-%d %H:%M:%S') if site.last_checked else None,
            'uptime': float(site.uptime),
            'check_interval': site.check_interval
        }
        serialized_sites.append(serialized_site)
    
    return jsonify(serialized_sites)

@app.route('/sites', methods=['POST'])
def add_site():
    data = request.get_json()
    new_url = data.get('url')
    new_type = data.get('type')
    check_interval = int(data.get('check_interval', 10))  # Default check interval 10 seconds

    if new_url and new_type and not Site.query.filter_by(url=new_url).first():
        new_site = Site(type=new_type, url=new_url, status=None, last_checked=None, uptime=0, check_interval=check_interval)
        db.session.add(new_site)
        db.session.commit()
        return jsonify({'message': 'Site added successfully'}), 201
    else:
        return jsonify({'error': 'Site already exists or invalid URL or type'}), 400

@app.route('/sites/<path:url>', methods=['DELETE'])
def delete_site(url):
    site = Site.query.filter_by(url=url).first()
    if site:
        db.session.delete(site)
        db.session.commit()
        return jsonify({'message': 'Site deleted successfully'}), 200
    else:
        return jsonify({'error': 'Site not found'}), 404

@app.route('/sites/<path:url>', methods=['PUT'])
def update_site(url):
    data = request.get_json()
    new_type = data.get('type')
    check_interval = int(data.get('check_interval', 10))

    site = Site.query.filter_by(url=url).first()
    if site:
        site.type = new_type if new_type else site.type
        site.check_interval = check_interval
        db.session.commit()
        return jsonify({'message': 'Site updated successfully'}), 200
    else:
        return jsonify({'error': 'Site not found'}), 404

if __name__ == '__main__':
    def monitor_sites():
        while True:
            update_sites_status()
            time.sleep(10)  # Check every 10 seconds

    monitor_thread = threading.Thread(target=monitor_sites)
    monitor_thread.start()

    app.run(host='0.0.0.0', port=5000, debug=True)
