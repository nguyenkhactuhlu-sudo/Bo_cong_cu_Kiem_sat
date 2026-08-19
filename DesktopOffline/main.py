"""Launcher WebView2 cho bộ công cụ offline trên Windows."""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import webview
from flask import Flask, send_from_directory
from werkzeug.serving import make_server

from tool_registry import TOOLS


APP_NAME = "Bộ công cụ Kiểm sát Offline"


def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))


def install_root() -> Path:
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else resource_root()


def configure_runtime() -> None:
    """Buộc WebView2 dùng runtime đi kèm khi có, không tải runtime từ mạng."""
    fixed_runtime = install_root() / "runtime" / "WebView2"
    if fixed_runtime.exists():
        os.environ["WEBVIEW2_BROWSER_EXECUTABLE_FOLDER"] = str(fixed_runtime)
    os.environ["BCKS_DESKTOP_OFFLINE"] = "1"


def load_source_module(source: Path):
    module_dir = source.parent
    tool_root = resource_root() / "Tool"
    for path in (str(module_dir), str(tool_root)):
        if path not in sys.path:
            sys.path.insert(0, path)
    unique_name = "bcks_tool_" + source.stem + "_" + str(abs(hash(str(source))))
    spec = importlib.util.spec_from_file_location(unique_name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Không thể nạp công cụ: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run_flask_tool(tool: dict) -> None:
    source = resource_root() / tool["source"]
    module = load_source_module(source)
    flask_app = module.app
    if tool.get("template_folder"):
        flask_app.template_folder = str(resource_root() / tool["template_folder"])
    if tool.get("static_folder"):
        flask_app.static_folder = str(resource_root() / tool["static_folder"])
    assets = resource_root() / "DesktopOfflineAssets"
    if assets.exists() and "offline_assets" not in flask_app.view_functions:
        flask_app.add_url_rule(
            "/__offline_assets/<path:filename>", "offline_assets",
            lambda filename: send_from_directory(assets, filename),
        )
    port = free_port()
    server = make_server("127.0.0.1", port, flask_app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        base_url = f"http://127.0.0.1:{port}"
        api = ToolApi(base_url)
        window = webview.create_window(
            tool["title"], f"http://127.0.0.1:{port}/",
            js_api=api, width=tool["width"], height=tool["height"], min_size=(860, 600),
        )
        api.window = window
        webview.start(gui="edgechromium", private_mode=True)
    finally:
        server.shutdown()


def run_html_tool(tool: dict) -> None:
    source = resource_root() / tool["source"]
    assets = resource_root() / "DesktopOfflineAssets"
    static_app = Flask("bcks_static_desktop", static_folder=None)

    @static_app.get("/")
    def page():
        return source.read_text(encoding="utf-8")

    @static_app.get("/__offline_assets/<path:filename>")
    def offline_assets(filename):
        return send_from_directory(assets, filename)

    @static_app.get("/static/<path:filename>")
    def shared_static(filename):
        return send_from_directory(resource_root() / tool["static_folder"], filename)

    port = free_port()
    server = make_server("127.0.0.1", port, static_app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    webview.create_window(
        tool["title"], f"http://127.0.0.1:{port}/",
        width=tool["width"], height=tool["height"], min_size=(860, 600),
    )
    try:
        webview.start(gui="edgechromium", private_mode=True)
    finally:
        server.shutdown()


class LauncherApi:
    def launch(self, tool_id: str) -> dict:
        if tool_id not in TOOLS:
            return {"ok": False, "message": "Không tìm thấy công cụ."}
        if getattr(sys, "frozen", False):
            command = [sys.executable, "--tool", tool_id]
        else:
            command = [sys.executable, str(Path(__file__).resolve()), "--tool", tool_id]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(command, cwd=str(install_root()), creationflags=flags)
        return {"ok": True}


class ToolApi:
    """Các thao tác hệ điều hành mà WebView không tự thực hiện được."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.window = None

    def choose_folder(self) -> dict:
        """Mở hộp thoại chọn thư mục Windows trên một tiến trình STA riêng.

        Folder dialog của pywebview có thể bị treo khi được gọi từ luồng xử lý
        JavaScript API. Windows PowerShell 5.1 luôn có sẵn trên các máy đích và
        cho phép gọi FolderBrowserDialog trên đúng luồng STA mà không cần mạng.
        """
        script = r"""
$OutputEncoding = [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Application]::EnableVisualStyles()
$owner = New-Object System.Windows.Forms.Form
$owner.TopMost = $true
$owner.ShowInTaskbar = $false
$owner.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual
$owner.Left = -32000
$owner.Top = -32000
$owner.Width = 1
$owner.Height = 1
$owner.Add_Shown({ $owner.Activate() })
$owner.Show()
$owner.Activate()
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = 'Chọn thư mục chứa các file cần đổi tên'
$dialog.ShowNewFolderButton = $false
if ($dialog.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {
    [Console]::Out.Write($dialog.SelectedPath)
}
$owner.Dispose()
"""
        encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        startupinfo = None
        if hasattr(subprocess, "STARTUPINFO"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
        try:
            completed = subprocess.run(
                [
                    "powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
                    "-STA", "-EncodedCommand", encoded_script,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=flags,
                startupinfo=startupinfo,
                timeout=600,
                check=False,
            )
        except Exception as error:
            return {"ok": False, "message": f"Không thể mở hộp thoại chọn thư mục: {error}"}
        if completed.returncode != 0:
            detail = completed.stderr.strip().lstrip("\ufeff")
            return {"ok": False, "message": "Không thể mở hộp thoại chọn thư mục" + (f": {detail}" if detail else ".")}
        selected = completed.stdout.strip().lstrip("\ufeff")
        if not selected:
            return {"ok": True, "cancelled": True, "path": ""}
        return {"ok": True, "cancelled": False, "path": str(Path(selected))}

    def save_anonymized(self, replacements: list) -> dict:
        if not isinstance(replacements, list):
            return {"ok": False, "message": "Danh sách thay thế không hợp lệ."}
        try:
            request = urllib.request.Request(
                self.base_url + "/export",
                data=json.dumps({"replacements": replacements}, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                document = response.read()
        except urllib.error.HTTPError as error:
            message = error.read().decode("utf-8", errors="replace")
            return {"ok": False, "message": message or f"Lỗi xuất file: HTTP {error.code}"}
        except Exception as error:
            return {"ok": False, "message": f"Không thể tạo file: {error}"}

        if not document:
            return {"ok": False, "message": "File xuất ra bị rỗng."}
        selected = self.window.create_file_dialog(
            webview.SAVE_DIALOG,
            directory=str(Path.home() / "Documents"),
            save_filename="van_ban_da_an_danh.docx",
            file_types=("Tài liệu Word (*.docx)",),
        )
        if not selected:
            return {"ok": True, "cancelled": True}
        target = Path(selected[0] if isinstance(selected, (list, tuple)) else selected)
        if target.suffix.lower() != ".docx":
            target = target.with_suffix(".docx")
        try:
            target.write_bytes(document)
        except OSError as error:
            return {"ok": False, "message": f"Không thể ghi file: {error}"}
        return {"ok": True, "cancelled": False, "path": str(target)}

    def _save_response(self, url: str, filename: str, file_types: tuple, body: dict | None = None) -> dict:
        try:
            data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers = {} if body is None else {"Content-Type": "application/json"}
            request = urllib.request.Request(url, data=data, headers=headers, method="GET" if body is None else "POST")
            with urllib.request.urlopen(request, timeout=120) as response:
                content = response.read()
        except Exception as error:
            return {"ok": False, "message": f"Không thể tải kết quả OCR: {error}"}
        selected = self.window.create_file_dialog(webview.SAVE_DIALOG, directory=str(Path.home() / "Documents"), save_filename=filename, file_types=file_types)
        if not selected:
            return {"ok": True, "cancelled": True}
        target = Path(selected[0] if isinstance(selected, (list, tuple)) else selected)
        if not target.suffix:
            target = target.with_suffix(Path(filename).suffix)
        try:
            target.write_bytes(content)
        except OSError as error:
            return {"ok": False, "message": f"Không thể ghi file: {error}"}
        return {"ok": True, "cancelled": False, "path": str(target)}

    def save_ocr_file(self, filename: str) -> dict:
        safe_name = Path(str(filename)).name
        suffix = Path(safe_name).suffix.lower()
        types = {".docx": ("Tài liệu Word (*.docx)",), ".md": ("Markdown (*.md)",), ".txt": ("Văn bản (*.txt)",)}.get(suffix, ("Tất cả tệp (*.*)",))
        return self._save_response(self.base_url + "/api/download/" + urllib.parse.quote(safe_name), safe_name, types)

    def save_ocr_zip(self, files: list) -> dict:
        return self._save_response(self.base_url + "/api/batch/download", "ket_qua_ocr_hang_loat.zip", ("Tệp ZIP (*.zip)",), {"files": files})


LAUNCHER_HTML = r"""<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Bộ công cụ Offline</title>
<style>
@font-face{font-family:"Be Vietnam Pro Offline";src:url("__FONT_REGULAR__") format("truetype");font-weight:400;font-display:block}
@font-face{font-family:"Be Vietnam Pro Offline";src:url("__FONT_SEMIBOLD__") format("truetype");font-weight:600;font-display:block}
@font-face{font-family:"Be Vietnam Pro Offline";src:url("__FONT_BOLD__") format("truetype");font-weight:700 900;font-display:block}
*{box-sizing:border-box}body,button{margin:0;color:#123454;font-family:"Be Vietnam Pro Offline",Arial,sans-serif;text-rendering:geometricPrecision;-webkit-font-smoothing:antialiased}body{min-height:100vh;background-image:linear-gradient(to bottom,rgba(238,245,251,1) 0%,rgba(238,245,251,.96) 48%,rgba(238,245,251,.42) 100%),url("/static/lotus.png");background-color:#eef5fb;background-position:center bottom;background-size:100% auto;background-repeat:no-repeat;background-attachment:fixed}button{background:transparent}
.shell{max-width:1180px;margin:auto;padding:30px;min-height:100vh}.head{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}.brand{display:flex;align-items:center;gap:16px}.brand img{width:72px;height:72px;object-fit:contain;filter:drop-shadow(0 4px 8px rgba(15,23,42,.15))}
h1{font-size:28px;margin:0 0 8px}.sub{color:#64748b;font-size:14px}.safe{background:#d1fae5;color:#047857;padding:8px 13px;border-radius:999px;font-weight:700;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}.card{grid-column:span 4;background:#fff;border:1px solid #c9dcef;border-top:4px solid #0757a6;border-radius:24px;padding:21px;min-height:165px;cursor:pointer;text-align:left;box-shadow:0 5px 18px rgba(6,59,115,.08);transition:.2s}
.card:hover{transform:translateY(-3px);box-shadow:0 15px 30px rgba(6,59,115,.15);border-color:#f2b705}.wide{grid-column:span 6}.badge{display:inline-block;background:#e7f2ff;color:#0757a6;border-radius:999px;padding:4px 9px;font-size:10px;font-weight:800;letter-spacing:.7px}.icon{float:right;font-size:27px;color:#0757a6}.title{font-size:17px;font-weight:800;margin:16px 0 7px}.desc{color:#55708b;font-size:13px;line-height:1.5}.privacy-notice{display:flex;align-items:center;justify-content:center;gap:12px;margin-top:22px;padding:14px 18px;border:1px solid #86d7b5;border-radius:16px;background:#ecfdf5;color:#065f46;font-size:13px}.privacy-icon{display:grid;place-items:center;width:32px;height:32px;border-radius:50%;background:#047857;color:#fff;font-size:16px;flex:0 0 auto}.privacy-notice strong{display:block;font-size:13px}.privacy-notice span{display:block;margin-top:2px;color:#28735c;font-size:12px}.foot{display:flex;align-items:center;justify-content:center;gap:8px;margin-top:18px;padding-top:14px;border-top:3px solid #f2b705;color:#0757a6;font-size:12px;font-weight:600;text-align:center}.foot img{height:30px;width:auto}
@media(max-width:800px){body{background-size:auto 42vh}.card,.wide{grid-column:span 12}.head{align-items:flex-start;gap:12px;flex-direction:column}.shell{padding:20px}}
</style></head><body><main class="shell"><header class="head"><div class="brand"><img src="__LOGO_DATA__" alt="Logo ngành Kiểm sát nhân dân"><div><h1>BỘ CÔNG CỤ KIỂM SÁT OFFLINE</h1><div class="sub">Chọn công cụ để mở trong một cửa sổ riêng</div></div></div><div class="safe">✓ XỬ LÝ TRÊN MÁY</div></header>
<section class="grid">
<button class="card" onclick="go('interest')"><span class="badge">NGOẠI TUYẾN</span><span class="icon">⌁</span><div class="title">Tự động tính tiền lãi</div><div class="desc">Tính lãi trong hạn, quá hạn và chậm trả.</div></button>
<button class="card" onclick="go('court_fee')"><span class="badge">NGOẠI TUYẾN</span><span class="icon">▥</span><div class="title">Tính án phí</div><div class="desc">Tra cứu và tính án phí hình sự, dân sự.</div></button>
<button class="card" onclick="go('deadline')"><span class="badge">NGOẠI TUYẾN</span><span class="icon">◷</span><div class="title">Tính tuổi — Thời hạn</div><div class="desc">Tính chính xác tuổi và thời hạn tố tụng.</div></button>
<button class="card wide" onclick="go('anonymizer')"><span class="badge">BẢO MẬT</span><span class="icon">▰</span><div class="title">Tự động che thông tin</div><div class="desc">Ẩn thông tin cá nhân trong văn bản Word trước khi chia sẻ.</div></button>
<button class="card wide" onclick="go('renamer')"><span class="badge">NGOẠI TUYẾN</span><span class="icon">✎</span><div class="title">Tự động đổi tên file</div><div class="desc">Chuẩn hóa hoặc đổi tên tài liệu hàng loạt.</div></button>
<button class="card wide" onclick="go('spell_checker')"><span class="badge">KHÔNG AI</span><span class="icon">✓</span><div class="title">Rà soát chính tả Word</div><div class="desc">Phát hiện lỗi và xuất bản Word đánh dấu hoặc đã sửa.</div></button>
<button class="card wide" onclick="go('ocr')"><span class="badge">TESSERACT</span><span class="icon">⌕</span><div class="title">Nhận dạng chữ PDF, ảnh</div><div class="desc">Xuất kết quả sang Word, Markdown hoặc TXT.</div></button>
</section><div class="privacy-notice"><div class="privacy-icon">✓</div><div><strong>Xử lý hoàn toàn cục bộ</strong><span>Dữ liệu chỉ được xử lý trên máy tính này</span></div></div><div class="foot">Phát triển bởi: <strong>Nguyễn Khắc Tú - Viện KSND khu vực 5 - Bắc Ninh</strong><img id="footer-logo" alt="Logo ngành Kiểm sát"></div></main>
<script>document.getElementById('footer-logo').src=document.querySelector('.brand img').src;async function go(id){try{const r=await window.pywebview.api.launch(id);if(!r.ok)alert(r.message)}catch(e){alert('Không thể mở công cụ: '+e)}}</script></body></html>"""


def run_launcher() -> None:
    logo = base64.b64encode((resource_root() / "static" / "logo_moi.png").read_bytes()).decode("ascii")
    def font_data(name: str) -> str:
        data = (resource_root() / "DesktopOfflineAssets" / "brand" / "fonts" / name).read_bytes()
        return "data:font/ttf;base64," + base64.b64encode(data).decode("ascii")
    html = LAUNCHER_HTML.replace("__LOGO_DATA__", f"data:image/png;base64,{logo}")
    html = html.replace("__FONT_REGULAR__", font_data("BeVietnamPro-Regular.ttf"))
    html = html.replace("__FONT_SEMIBOLD__", font_data("BeVietnamPro-SemiBold.ttf"))
    html = html.replace("__FONT_BOLD__", font_data("BeVietnamPro-Bold.ttf"))
    launcher_app = Flask("bcks_launcher_desktop", static_folder=None)

    @launcher_app.get("/")
    def launcher_page():
        return html

    @launcher_app.get("/static/<path:filename>")
    def launcher_static(filename):
        return send_from_directory(resource_root() / "static", filename)

    port = free_port()
    server = make_server("127.0.0.1", port, launcher_app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    webview.create_window(
        APP_NAME, f"http://127.0.0.1:{port}/", js_api=LauncherApi(),
        width=1160, height=780, min_size=(820, 620),
    )
    try:
        webview.start(gui="edgechromium", private_mode=True)
    finally:
        server.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--tool", choices=sorted(TOOLS))
    args = parser.parse_args()
    configure_runtime()
    if args.tool:
        tool = TOOLS[args.tool]
        run_html_tool(tool) if tool["kind"] == "html" else run_flask_tool(tool)
    else:
        run_launcher()


if __name__ == "__main__":
    main()
