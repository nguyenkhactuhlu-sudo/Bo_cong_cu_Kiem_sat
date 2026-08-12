"""Khởi chạy Flask trên localhost và mở đúng cổng ứng dụng."""

import json
import socket
import threading
import time
import urllib.request
import webbrowser

from flask import jsonify
from werkzeug.serving import make_server


def run_desktop_app(app, app_id, preferred_port, path="/", host="127.0.0.1", open_browser=True):
    endpoint = "/__health"
    holder = {}

    if endpoint not in {rule.rule for rule in app.url_map.iter_rules()}:
        def health():
            server = holder.get("server")
            return jsonify(ok=True, app_id=app_id, port=server.server_port if server else None)
        app.add_url_rule(endpoint, endpoint=f"health_{app_id.replace('-', '_')}", view_func=health)

    try:
        with socket.create_connection((host, preferred_port), timeout=0.2):
            busy = True
    except OSError:
        busy = False
    server = make_server(host, 0 if busy else preferred_port, app, threaded=True)
    holder["server"] = server
    url = f"http://{host}:{server.server_port}{path}"

    def open_when_ready():
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://{host}:{server.server_port}{endpoint}", timeout=0.5) as response:
                    if json.loads(response.read()).get("app_id") == app_id:
                        webbrowser.open(url)
                        return
            except Exception:
                time.sleep(0.1)

    if open_browser:
        threading.Thread(target=open_when_ready, daemon=True).start()
    # Tránh lỗi mã hóa ở một số Windows console dùng CP-1252 khi chạy EXE portable.
    print(f"Ung dung dang chay tai: {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
