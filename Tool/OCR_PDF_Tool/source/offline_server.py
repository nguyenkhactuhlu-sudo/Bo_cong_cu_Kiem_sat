"""Khởi chạy Flask desktop an toàn, không mở nhầm ứng dụng trên cổng cũ."""

import json
import socket
import threading
import time
import urllib.request
import webbrowser

from flask import jsonify
from werkzeug.serving import make_server


def run_desktop_app(app, app_id, preferred_port, path='/', host='127.0.0.1',
                    open_browser=True, threaded=True):
    """Bind server trước, lấy đúng cổng thực tế rồi mới mở trình duyệt."""

    endpoint = '/__health'
    if endpoint not in {rule.rule for rule in app.url_map.iter_rules()}:
        app.add_url_rule(
            endpoint,
            endpoint=f'health_{app_id.replace("-", "_")}',
            view_func=lambda: jsonify({
                'ok': True,
                'app_id': app_id,
                'port': server.server_port,
            }),
            methods=['GET'],
        )

    try:
        with socket.create_connection((host, preferred_port), timeout=0.25):
            preferred_port_busy = True
    except OSError:
        preferred_port_busy = False

    try:
        server = make_server(host, 0 if preferred_port_busy else preferred_port,
                             app, threaded=threaded)
    except OSError:
        # Cổng ưu tiên đang bận: hệ điều hành cấp một cổng trống và giữ socket.
        server = make_server(host, 0, app, threaded=threaded)

    port = server.server_port
    base_url = f'http://{host}:{port}'
    target_url = base_url + (path if path.startswith('/') else '/' + path)

    def open_when_ready():
        health_url = base_url + endpoint
        for _ in range(60):
            try:
                with urllib.request.urlopen(health_url, timeout=0.5) as response:
                    payload = json.loads(response.read().decode('utf-8'))
                if payload.get('app_id') == app_id:
                    webbrowser.open(target_url)
                    return
            except Exception:
                time.sleep(0.1)

    if open_browser:
        threading.Thread(target=open_when_ready, daemon=True).start()

    print(f'  App ID: {app_id}')
    print(f'  Server: {target_url}')
    if port != preferred_port:
        print(f'  Cong {preferred_port} dang ban; da chuyen sang cong {port}.')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
