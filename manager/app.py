from flask import Flask, request, render_template_string, redirect, url_for, flash
import json
import os
import socket
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = 'super-secret-key-for-flash-messages'
TARGETS_FILE = '/data/targets.json'

# --- ฟังก์ชันตรวจสอบ URL จริง (Validation) ---
def is_valid_domain(url):
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, "Invalid URL format (Must start with http:// or https://)"
        
        # ลอง Resolve DNS ดูว่ามีจริงไหม
        domain = parsed.netloc.split(':')[0] # ตัด port ออกถ้ามี
        socket.gethostbyname(domain)
        return True, "Valid"
    except socket.gaierror:
        return False, f"Domain '{domain}' not found or unreachable."
    except Exception as e:
        return False, str(e)

# --- HTML TEMPLATE (Design: Grouped Services + Fixed Colors) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Service Command Center</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #111217;
            --card-bg: #181b1f;
            --text-main: #d8d9da;
            --text-muted: #8e8e8e;
            --primary: #3274d9;
            --primary-hover: #245bbf;
            --danger: #ff4d4f;
            --border: #2c3235;
            --input-bg: #0b0c0e;
        }
        
        * { box-sizing: border-box; }

        body { 
            font-family: 'Inter', sans-serif; 
            background-color: var(--bg-color); 
            color: var(--text-main); 
            margin: 0; 
            padding: 20px; 
            overflow-y: auto; 
        }

        .alert {
            padding: 12px 16px;
            background-color: rgba(255, 77, 79, 0.15);
            border: 1px solid var(--danger);
            color: #ffccc7;
            border-radius: 6px;
            margin-bottom: 20px;
            font-size: 13px;
            display: flex; align-items: center;
        }
        
        .control-panel {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 30px;
            display: flex; flex-wrap: wrap; gap: 15px; align-items: flex-end;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .form-group { display: flex; flex-direction: column; gap: 8px; flex-grow: 1; min-width: 250px; }
        label { font-size: 11px; color: var(--text-muted); font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; }
        
        input {
            background: var(--input-bg); border: 1px solid var(--border); color: white;
            padding: 12px 16px; border-radius: 6px; font-size: 14px; outline: none; width: 100%; transition: all 0.2s;
        }
        input:focus { border-color: var(--primary); box-shadow: 0 0 0 2px rgba(50, 116, 217, 0.2); }

        button.btn-add {
            background: var(--primary); color: white; border: none;
            padding: 0 28px; border-radius: 6px; font-weight: 600; cursor: pointer;
            height: 42px; white-space: nowrap; transition: all 0.2s; font-size: 14px;
        }
        button.btn-add:hover { background: var(--primary-hover); transform: translateY(-1px); }

        /* --- List Design Fixed --- */
        .list-header { font-size: 12px; color: var(--text-muted); font-weight: 700; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
        
        .service-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center; 
            transition: border-color 0.2s;
            flex-wrap: nowrap; 
        }
        .service-card:hover { border-color: #444; }

        .service-info { 
            display: flex; 
            flex-direction: column; 
            gap: 4px; 
            overflow: hidden; 
            margin-right: 15px;
        }
        .service-name { font-size: 16px; font-weight: 600; color: #fff; }
        .service-url { font-size: 12px; color: var(--text-muted); font-family: monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        /* Container ด้านขวา (ป้าย + ปุ่มลบ) */
        .right-actions {
            display: flex;
            align-items: center;
            gap: 15px; 
            flex-shrink: 0; 
        }

        .monitor-badges { display: flex; gap: 6px; }
        
        /* --- Badge Colors Fixed --- */
        .badge {
            font-size: 10px; font-weight: 800; padding: 4px 8px; border-radius: 4px;
            text-transform: uppercase; letter-spacing: 0.5px;
            border: 1px solid transparent;
        }
        
        /* สีแยกตาม Layer */
        .badge.app { background: rgba(6, 182, 212, 0.15); color: #22d3ee; border-color: rgba(6, 182, 212, 0.3); }
        .badge.tcp { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: rgba(245, 158, 11, 0.3); }
        .badge.infra { background: rgba(236, 72, 153, 0.15); color: #f472b6; border-color: rgba(236, 72, 153, 0.3); }

        button.btn-delete {
            background: transparent;
            color: var(--danger);
            border: 1px solid var(--border);
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
            height: 34px; 
            display: flex;
            align-items: center;
        }
        button.btn-delete:hover {
            background: var(--danger);
            color: white;
            border-color: var(--danger);
        }

        .empty-state { padding: 60px; text-align: center; color: var(--text-muted); font-size: 14px; border: 2px dashed var(--border); border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="alert">⚠️ {{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div class="control-panel">
            <div class="form-group">
                <label>Target URL</label>
                <input type="text" name="url" form="addForm" placeholder="https://example.com" required autocomplete="off">
            </div>
            <div class="form-group">
                <label>Service Name</label>
                <input type="text" name="service" form="addForm" placeholder="e.g. Google" required autocomplete="off">
            </div>
            <div style="flex-grow: 0;">
                <form id="addForm" action="/add" method="post" style="margin:0;">
                    <button type="submit" class="btn-add">Add Monitor</button>
                </form>
            </div>
        </div>

        <div class="list-header">Monitored Services</div>
        
        {% if grouped_services %}
            {% for service_name, details in grouped_services.items() %}
            <div class="service-card">
                <div class="service-info">
                    <span class="service-name">{{ service_name }}</span>
                    <span class="service-url">{{ details.url }}</span>
                </div>
                
                <div class="right-actions">
                    <div class="monitor-badges">
                        <span class="badge app">APP</span>
                        <span class="badge tcp">TCP</span>
                        <span class="badge infra">INFRA</span>
                    </div>

                    <form action="/delete" method="post" style="margin:0;">
                        <input type="hidden" name="service" value="{{ service_name }}">
                        <button type="submit" class="btn-delete">Delete</button>
                    </form>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="empty-state">No services configured. Add a target to begin monitoring.</div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    data = []
    grouped_services = {}

    if os.path.exists(TARGETS_FILE):
        try:
            with open(TARGETS_FILE, 'r') as f:
                # แก้ไข: เพิ่ม try-except ดักจับไฟล์ JSON พัง
                content = f.read()
                if content.strip():
                    data = json.loads(content)
        except Exception as e:
            print(f"Error loading JSON: {e}")
            data = []

    # จัดกลุ่มข้อมูลเพื่อแสดงผล
    for item in data:
        try:
            # แก้ไข: เพิ่มเช็คว่ามี key ครบไหม ป้องกัน error 'service' not in 'labels'
            if 'labels' not in item or 'service' not in item['labels']:
                continue

            svc_name = item['labels']['service']
            
            if svc_name not in grouped_services:
                grouped_services[svc_name] = {'url': 'Unknown URL', 'layers': []}
            
            if item['labels'].get('layer') == 'application':
                grouped_services[svc_name]['url'] = item['targets'][0]
            
            grouped_services[svc_name]['layers'].append(item['labels']['layer'])
        except:
            continue

    return render_template_string(HTML_TEMPLATE, grouped_services=grouped_services)

@app.route('/add', methods=['POST'])
def add_target():
    full_url = request.form.get('url')
    service_name = request.form.get('service')
    
    # 1. Validation
    valid, message = is_valid_domain(full_url)
    if not valid:
        flash(f"Error: {message}")
        return redirect(url_for('index'))

    # 2. Prepare Data
    try:
        parsed = urlparse(full_url)
        domain = parsed.netloc
        if not domain: domain = full_url.split('/')[0]

        new_entries = [
            { "targets": [full_url], "labels": { "service": service_name, "layer": "application", "module": "http_2xx" } },
            { "targets": [f"{domain}:443"], "labels": { "service": service_name, "layer": "transport", "module": "tcp_connect" } },
            { "targets": [domain], "labels": { "service": service_name, "layer": "infrastructure", "module": "icmp" } }
        ]
        
        # 3. Save to JSON
        data = []
        if os.path.exists(TARGETS_FILE):
            try:
                with open(TARGETS_FILE, 'r') as f:
                    data = json.load(f)
            except: data = []
        
        data.extend(new_entries)
        
        with open(TARGETS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
            
    except Exception as e:
        flash(f"System Error: {str(e)}")
        
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_target():
    service_name = request.form.get('service')
    
    if os.path.exists(TARGETS_FILE):
        try:
            with open(TARGETS_FILE, 'r') as f: data = json.load(f)
            # ลบทุกรายการที่มีชื่อ service ตรงกัน
            data = [i for i in data if i.get('labels', {}).get('service') != service_name]
            with open(TARGETS_FILE, 'w') as f: json.dump(data, f, indent=4)
        except:
            pass
            
    return redirect(url_for('index'))

if __name__ == '__main__':
    # เปิด Debug Mode เพื่อให้เห็น Error ไม่ใช่หน้าขาว
    app.run(host='0.0.0.0', port=5000, debug=True)