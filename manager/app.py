from flask import Flask, request, render_template_string, redirect, url_for, Response
from functools import wraps
import json
import os
from urllib.parse import urlparse

app = Flask(__name__)
TARGETS_FILE = '/data/targets.json'

# --- Admin Credentials ---
USERNAME = "admin"
PASSWORD = "password1234"

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response('Login Required', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# --- HTML TEMPLATE (GRAFANA DARK THEME STYLE) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Service Manager</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        /* Grafana Dark Theme Colors */
        :root {
            --bg-color: #111217; /* สีพื้นหลัง Grafana */
            --card-bg: #181b1f;  /* สีการ์ด */
            --text-main: #d8d9da;
            --text-muted: #8e8e8e;
            --primary: #3274d9;  /* สีฟ้า Grafana */
            --primary-hover: #245bbf;
            --danger: #ff4d4f;   /* สีแดง */
            --border: #2c3235;
            --input-bg: #0b0c0e;
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            /* ซ่อน Scrollbar ถ้าไม่จำเป็น เพื่อความเนียน */
            overflow-y: auto; 
        }

        /* ปรับแต่ง Scrollbar ให้มืดเนียนไปกับ Theme */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-color); }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #555; }

        .container { max-width: 900px; margin: 0 auto; }
        
        h2 { 
            font-size: 18px; 
            font-weight: 500; 
            margin-bottom: 20px; 
            color: var(--text-main);
            border-bottom: 1px solid var(--primary);
            padding-bottom: 10px;
            display: inline-block;
        }

        /* Input Form Style */
        .control-panel {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 25px;
            display: flex;
            gap: 15px;
            align-items: flex-end;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }

        .form-group { display: flex; flex-direction: column; gap: 8px; flex: 1; }
        label { font-size: 12px; color: var(--text-muted); font-weight: 600; }
        
        input {
            background: var(--input-bg);
            border: 1px solid var(--border);
            color: white;
            padding: 10px;
            border-radius: 4px;
            font-size: 14px;
            outline: none;
            transition: border 0.2s;
        }
        input:focus { border-color: var(--primary); }

        button.btn-add {
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 4px;
            font-weight: 500;
            cursor: pointer;
            height: 40px; /* ให้เท่า Input */
            transition: background 0.2s;
        }
        button.btn-add:hover { background: var(--primary-hover); }

        /* Table / List Style */
        .list-container {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 4px;
        }

        .list-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 20px;
            border-bottom: 1px solid var(--border);
            transition: background 0.2s;
        }
        .list-item:last-child { border-bottom: none; }
        .list-item:hover { background: rgba(255,255,255,0.03); }

        .item-info { display: flex; align-items: center; gap: 15px; }
        .service-name { font-weight: 600; color: #fff; min-width: 100px; }
        .target-url { color: var(--text-muted); font-size: 13px; font-family: monospace; }

        /* Tags for Layers */
        .tag { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; border: 1px solid transparent;}
        .tag.app { background: rgba(50, 116, 217, 0.2); color: #5b9bf5; border-color: rgba(50, 116, 217, 0.3); }
        .tag.trans { background: rgba(235, 123, 24, 0.2); color: #ff9830; border-color: rgba(235, 123, 24, 0.3); }
        .tag.infra { background: rgba(137, 31, 194, 0.2); color: #c069ff; border-color: rgba(137, 31, 194, 0.3); }

        button.btn-delete {
            background: transparent;
            color: var(--danger);
            border: 1px solid var(--border);
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }
        button.btn-delete:hover { background: rgba(255, 77, 79, 0.1); border-color: var(--danger); }
        
        .empty-state { padding: 40px; text-align: center; color: var(--text-muted); font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <div class="control-panel">
            <div class="form-group">
                <label>TARGET URL</label>
                <input type="text" name="url" form="addForm" placeholder="https://example.com" required autocomplete="off">
            </div>
            <div class="form-group">
                <label>SERVICE NAME</label>
                <input type="text" name="service" form="addForm" placeholder="e.g. Finance" required autocomplete="off">
            </div>
            <form id="addForm" action="/add" method="post" style="margin:0;">
                <button type="submit" class="btn-add">+ Add Service</button>
            </form>
        </div>

        <h2>Active Monitors</h2>
        <div class="list-container">
            {% for item in targets %}
            <div class="list-item">
                <div class="item-info">
                    <span class="service-name">{{ item.labels.service }}</span>
                    {% if item.labels.layer == 'application' %}<span class="tag app">APP</span>
                    {% elif item.labels.layer == 'transport' %}<span class="tag trans">TCP</span>
                    {% else %}<span class="tag infra">INFRA</span>{% endif %}
                    <span class="target-url">{{ item.targets[0] }}</span>
                </div>
                
                <form action="/delete" method="post" style="margin:0;">
                    <input type="hidden" name="target" value="{{ item.targets[0] }}">
                    <input type="hidden" name="service" value="{{ item.labels.service }}">
                    <input type="hidden" name="layer" value="{{ item.labels.layer }}">
                    <button type="submit" class="btn-delete">Remove</button>
                </form>
            </div>
            {% endfor %}
            
            {% if not targets %}
            <div class="empty-state">No active services. Add one above to start monitoring.</div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
@requires_auth
def index():
    data = []
    if os.path.exists(TARGETS_FILE):
        with open(TARGETS_FILE, 'r') as f:
            try: data = json.load(f)
            except: data = []
    return render_template_string(HTML_TEMPLATE, targets=data)

@app.route('/add', methods=['POST'])
@requires_auth
def add_target():
    full_url = request.form.get('url')
    service_name = request.form.get('service')
    
    parsed = urlparse(full_url)
    domain = parsed.netloc
    if not domain: domain = full_url.split('/')[0]

    # Auto generate 3 layers
    new_entries = [
        { "targets": [full_url], "labels": { "service": service_name, "layer": "application", "module": "http_2xx" } },
        { "targets": [f"{domain}:443"], "labels": { "service": service_name, "layer": "transport", "module": "tcp_connect" } },
        { "targets": ["8.8.8.8"], "labels": { "service": service_name, "layer": "infrastructure", "module": "icmp" } }
    ]
    
    data = []
    if os.path.exists(TARGETS_FILE):
        with open(TARGETS_FILE, 'r') as f:
            try: data = json.load(f)
            except: data = []
    data.extend(new_entries)
    with open(TARGETS_FILE, 'w') as f: json.dump(data, f, indent=4)
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
@requires_auth
def delete_target():
    target = request.form.get('target')
    service = request.form.get('service')
    layer = request.form.get('layer')
    
    if os.path.exists(TARGETS_FILE):
        with open(TARGETS_FILE, 'r') as f: data = json.load(f)
        data = [i for i in data if not (i['targets'][0] == target and i['labels']['service'] == service and i['labels']['layer'] == layer)]
        with open(TARGETS_FILE, 'w') as f: json.dump(data, f, indent=4)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)