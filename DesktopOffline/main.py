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
function Activate-Window([IntPtr]$hwnd) {
    Add-Type -Namespace Win32 -Name Native -MemberDefinition @'
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
[DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
'@
    [Win32.Native]::BringWindowToTop($hwnd) | Out-Null
    [Win32.Native]::SetForegroundWindow($hwnd) | Out-Null
}
# Form owner nho, trong suot, dat giua man hinh de dialog co owner hop le
# va Windows cho phep hien len foreground (khong dat off-screen).
$owner = New-Object System.Windows.Forms.Form
$owner.TopMost = $true
$owner.ShowInTaskbar = $false
$owner.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None
$owner.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
$owner.Width = 1
$owner.Height = 1
$owner.Opacity = 0.01
$owner.AllowTransparency = $true
$owner.Add_Shown({ $owner.Activate(); Activate-Window $owner.Handle })
$owner.Show()
$owner.Activate()
Activate-Window $owner.Handle
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = 'Chọn thư mục chứa các file cần đổi tên'
$dialog.ShowNewFolderButton = $false
$dialog.UseDescriptionForTitle = $true
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

    def _save_path_dialog(self, filename: str, file_types: tuple) -> dict:
        """Mở hộp thoại Lưu file của Windows trên một tiến trình STA riêng.

        create_file_dialog của pywebview có thể bị treo khi được gọi từ luồng
        xử lý JavaScript API (cùng vấn đề với FolderBrowserDialog). PowerShell
        5.1 luôn có sẵn trên máy đích và cho phép gọi SaveFileDialog trên đúng
        luồng STA mà không cần mạng.
        """
        file_type_list = "|".join(f"{label}|{pattern}" for label, pattern in file_types)
        escaped_name = filename.replace("'", "''")
        escaped_types = file_type_list.replace("'", "''")
        script = f"""
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
$owner.Add_Shown({{ $owner.Activate() }})
$owner.Show()
$owner.Activate()
$dialog = New-Object System.Windows.Forms.SaveFileDialog
$dialog.Filter = '{escaped_types}'
$dialog.FileName = '{escaped_name}'
$dialog.InitialDirectory = [Environment]::GetFolderPath('MyDocuments')
$dialog.OverwritePrompt = $true
if ($dialog.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {{
    [Console]::Out.Write($dialog.FileName)
}}
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
            return {"ok": False, "message": f"Không thể mở hộp thoại lưu file: {error}"}
        if completed.returncode != 0:
            detail = completed.stderr.strip().lstrip("\ufeff")
            return {"ok": False, "message": "Không thể mở hộp thoại lưu file" + (f": {detail}" if detail else ".")}
        selected = completed.stdout.strip().lstrip("\ufeff")
        if not selected:
            return {"ok": True, "cancelled": True}
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
        dialog = self._save_path_dialog(
            "van_ban_da_an_danh.docx",
            (("Tài liệu Word (*.docx)", "*.docx"),),
        )
        if not dialog.get("ok"):
            return dialog
        if dialog.get("cancelled"):
            return {"ok": True, "cancelled": True}
        target = Path(dialog["path"])
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
        dialog = self._save_path_dialog(filename, tuple(file_types))
        if not dialog.get("ok"):
            return dialog
        if dialog.get("cancelled"):
            return {"ok": True, "cancelled": True}
        target = Path(dialog["path"])
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


LAUNCHER_HTML = r"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bộ công cụ Kiểm sát Offline — Demo giao diện mới</title>
<style>
@font-face{font-family:"Be Vietnam Pro Offline";src:url("__FONT_REGULAR__") format("truetype");font-weight:400}
@font-face{font-family:"Be Vietnam Pro Offline";src:url("__FONT_SEMIBOLD__") format("truetype");font-weight:600}
@font-face{font-family:"Be Vietnam Pro Offline";src:url("__FONT_BOLD__") format("truetype");font-weight:700 900}
*{box-sizing:border-box;margin:0;padding:0}
body{
  font-family:"Be Vietnam Pro Offline",Arial,sans-serif;
  color:#123454;min-height:100vh;
  background-color:#eef5fb;
  background-image:
    radial-gradient(1200px 500px at 85% -10%, rgba(7,87,166,.10), transparent 60%),
    radial-gradient(900px 400px at -10% 110%, rgba(6,182,212,.08), transparent 60%),
    linear-gradient(to bottom, rgba(238,245,251,1) 0%, rgba(238,245,251,.96) 55%, rgba(238,245,251,.40) 100%),
    url("/static/lotus.png");
  background-position:center bottom;
  background-size:100% auto;
  background-repeat:no-repeat;
  background-attachment:fixed;
  -webkit-font-smoothing:antialiased;
}

/* ===== HEADER ===== */
.header{
  display:flex;justify-content:space-between;align-items:center;gap:20px;
  padding:22px 0;margin-bottom:10px;flex-wrap:wrap;
}
.brand{display:flex;align-items:center;gap:18px}
.brand-logo{
  width:78px;height:78px;border-radius:22px;object-fit:contain;
  background:linear-gradient(145deg,#fff,rgba(255,255,255,.6));
  padding:9px;border:1px solid #c9dcef;
  box-shadow:0 8px 20px rgba(7,87,166,.12);
}
.brand-name{font-size:27px;font-weight:800;letter-spacing:.4px;line-height:1.15}
.brand-name em{font-style:normal;color:#0757a6}
.brand-sub{color:#64748b;font-size:13.5px;margin-top:4px;font-weight:500}

.header-right{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.safe-badge{
  display:inline-flex;align-items:center;gap:8px;
  background:linear-gradient(135deg,#d1fae5,#a7f3d0);
  color:#047857;font-weight:700;font-size:12.5px;
  padding:8px 15px;border-radius:999px;
  border:1px solid #86efac;box-shadow:0 4px 12px rgba(5,150,105,.12);
}
.safe-badge .dot{width:8px;height:8px;border-radius:50%;background:#059669;box-shadow:0 0 0 3px rgba(5,150,105,.18);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

.search-box{
  position:relative;display:flex;align-items:center;
  background:#fff;border:1px solid #c9dcef;border-radius:14px;
  padding:0 14px;box-shadow:0 4px 14px rgba(7,87,166,.06);
  transition:border-color .2s, box-shadow .2s;
}
.search-box:focus-within{border-color:#0757a6;box-shadow:0 4px 18px rgba(7,87,166,.15)}
.search-box svg{flex-shrink:0;color:#94a3b8}
.search-box input{
  border:none;outline:none;background:transparent;
  padding:12px 12px;width:240px;font-family:inherit;
  font-size:13.5px;color:#123454;
}
.search-box input::placeholder{color:#94a3b8}

/* ===== SECTION TIÊU ĐỀ ===== */
.section-title{
  display:flex;align-items:center;gap:14px;
  margin:26px 0 16px;
}
.section-title .stripe{width:5px;height:26px;border-radius:3px;background:linear-gradient(180deg,#0757a6,#06b6d4)}
.section-title h2{font-size:16px;font-weight:800;color:#0f2f54}
.section-title .count{margin-left:auto;font-size:12.5px;font-weight:700;color:#64748b;background:#e7f2ff;padding:5px 12px;border-radius:999px}
.section-title .count b{color:#0757a6}

/* ===== GRID ===== */
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}

.card{
  grid-column:span 4;position:relative;overflow:hidden;
  background:rgba(236,246,255,.88);backdrop-filter:blur(6px);
  border:1px solid #c9dcef;border-radius:24px;
  padding:22px 22px 20px;min-height:176px;cursor:pointer;text-align:left;
  box-shadow:0 6px 20px rgba(6,59,115,.08),0 1px 3px rgba(6,59,115,.04);
  transition:transform .25s cubic-bezier(.4,0,.2,1), box-shadow .25s, border-color .25s;
  animation:fadeUp .5s ease both;
}
.card:nth-child(2){animation-delay:.05s}.card:nth-child(3){animation-delay:.1s}
.card:nth-child(4){animation-delay:.15s}.card:nth-child(5){animation-delay:.2s}
.card:nth-child(6){animation-delay:.25s}.card:nth-child(7){animation-delay:.3s}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.card.wide{grid-column:span 6}
.card:hover{
  transform:translateY(-5px) scale(1.01);
  box-shadow:0 20px 40px rgba(7,87,166,.18),0 4px 8px rgba(6,59,115,.06);
}
.card::before{
  content:'';position:absolute;inset:100% 0 0 0;opacity:.08;transition:inset .3s ease;
  background:linear-gradient(160deg,#0757a6,#06b6d4);
}
.card:hover::before{inset:55% 0 0 0}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;position:relative;z-index:1}
.card-illust{
  width:52px;height:52px;border-radius:16px;display:grid;place-items:center;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.6),0 4px 12px rgba(6,59,115,.10);
}
.card-illust svg{width:28px;height:28px}
.badge{
  display:inline-block;padding:5px 10px;border-radius:999px;
  font-size:10px;font-weight:800;letter-spacing:1px;text-transform:uppercase;
}
.badge-calc{background:#e0f2fe;color:#0369a1}
.badge-doc{background:#ecfeff;color:#0e7490}
.badge-sec{background:#fdf4ff;color:#a21caf}
.card:hover .badge{box-shadow:0 2px 8px rgba(7,87,166,.08)}
.card-title{font-size:17px;font-weight:800;margin:16px 0 7px;color:#0f2f54;position:relative;z-index:1}
.card-desc{color:#55708b;font-size:13px;line-height:1.55;position:relative;z-index:1}
.card-footer{
  margin-top:14px;padding-top:12px;border-top:1px dashed #d8e6f3;
  display:flex;align-items:center;gap:6px;
  font-size:11.5px;color:#64748b;font-weight:600;
  position:relative;z-index:1;
}
.card-footer .arrow{margin-left:auto;transition:transform .2s;color:#0757a6}
.card:hover .card-footer .arrow{transform:translateX(4px)}

/* ===== PRIVACY NOTICE ===== */
.privacy-notice{
  display:flex;align-items:center;gap:16px;
  margin-top:30px;padding:16px 22px;
  background:linear-gradient(135deg, rgba(236,253,245,.95), rgba(240,253,250,.85));
  border:1px solid #86d7b5;border-radius:18px;
  box-shadow:0 6px 18px rgba(5,150,105,.08);
}
.privacy-icon{
  flex:0 0 auto;width:38px;height:38px;border-radius:50%;
  display:grid;place-items:center;background:#047857;color:#fff;font-size:18px;
  box-shadow:0 4px 10px rgba(4,120,87,.25);
}
.privacy-notice strong{font-size:13.5px;color:#065f46;display:block}
.privacy-notice span{color:#28735c;font-size:12.5px;display:block;margin-top:2px}

/* ===== FOOTER ===== */
.foot{
  display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;
  margin-top:22px;padding-top:16px;border-top:3px solid #f2b705;
  color:#0757a6;font-size:12.5px;font-weight:600;text-align:center;
}
.foot img{height:30px;width:auto}

@media(max-width:900px){.card,.card.wide{grid-column:span 6}}
@media(max-width:640px){
  .card,.card.wide{grid-column:span 12}
  .search-box input{width:150px}
  .header{flex-direction:column;align-items:flex-start}
  body{background-size:auto 38vh}
}
</style>
</head>
<body>
<div style="max-width:1180px;margin:auto;padding:28px;min-height:100vh">

  <!-- HEADER -->
  <header class="header">
    <div class="brand">
      <img class="brand-logo" src="__LOGO_DATA__" alt="Logo ngành Kiểm sát nhân dân">
      <div>
        <div class="brand-name">BỘ CÔNG CỤ <em>KIỂM SÁT</em> OFFLINE</div>
        <div class="brand-sub">Chọn công cụ để mở trong một cửa sổ riêng</div>
      </div>
    </div>
    <div class="header-right">
      <div class="search-box">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.35-4.35"/></svg>
        <input type="text" id="searchInput" placeholder="Tìm công cụ..." oninput="filterTools()">
      </div>
      <div class="safe-badge"><span class="dot"></span> XỬ LÝ TRÊN MÁY</div>
    </div>
  </header>

  <!-- NHÓM TÍNH TOÁN -->
  <div class="section-title" data-section="calc">
    <span class="stripe"></span>
    <h2>TÍNH TOÁN NGHIỆP VỤ</h2>
    <span class="count"><b>3</b> công cụ</span>
  </div>
  <section class="grid calc-grid">
    <button class="card" data-name="tiền lãi" onclick="go('interest')">
      <div class="card-top">
        <span class="badge badge-calc">Tính toán</span>
        <div class="card-illust" style="background:linear-gradient(135deg,#e0f2fe,#bae6fd)">
          <svg viewBox="0 0 24 24" fill="none" stroke="#0369a1" stroke-width="2"><path class="anim-chart" d="M4 20h16M6 16l4-5 3 3 5-7" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
      </div>
      <div class="card-title">Tự động tính tiền lãi</div>
      <div class="card-desc">Lãi trong hạn, quá hạn và chậm trả theo Nghị quyết 01/2019.</div>
      <div class="card-footer">Ngoại tuyến · Nghị quyết 01/2019 <span class="arrow">→</span></div>
    </button>

    <button class="card" data-name="án phí" onclick="go('court_fee')">
      <div class="card-top">
        <span class="badge badge-calc">Tính toán</span>
        <div class="card-illust" style="background:linear-gradient(135deg,#ede9fe,#ddd6fe)">
          <svg viewBox="0 0 24 24" fill="none" stroke="#6d28d9" stroke-width="2"><rect x="4" y="3" width="16" height="5" rx="1"/><path d="M6 8v9a2 2 0 002 2h8a2 2 0 002-2V8M10 12h4" stroke-linecap="round"/></svg>
        </div>
      </div>
      <div class="card-title">Tính án phí</div>
      <div class="card-desc">Tra cứu và tính án phí hình sự, dân sự theo Nghị quyết 326.</div>
      <div class="card-footer">Ngoại tuyến · Nghị quyết 326 <span class="arrow">→</span></div>
    </button>

    <button class="card" data-name="tuổi thời hạn" onclick="go('deadline')">
      <div class="card-top">
        <span class="badge badge-calc">Tính toán</span>
        <div class="card-illust" style="background:linear-gradient(135deg,#fef3c7,#fde68a)">
          <svg viewBox="0 0 24 24" fill="none" stroke="#b45309" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2" stroke-linecap="round"/></svg>
        </div>
      </div>
      <div class="card-title">Tính tuổi — Thời hạn</div>
      <div class="card-desc">Tuổi, tạm giữ, tạm giam và thời hạn tố tụng chính xác.</div>
      <div class="card-footer">Ngoại tuyến · BLTTHS <span class="arrow">→</span></div>
    </button>
  </section>

  <!-- NHÓM XỬ LÝ TÀI LIỆU -->
  <div class="section-title" data-section="doc">
    <span class="stripe" style="background:linear-gradient(180deg,#0e7490,#06b6d4)"></span>
    <h2>XỬ LÝ TÀI LIỆU</h2>
    <span class="count"><b>4</b> công cụ</span>
  </div>
  <section class="grid doc-grid">
    <button class="card wide" data-name="che thông tin" onclick="go('anonymizer')">
      <div class="card-top">
        <span class="badge badge-sec">Bảo mật</span>
        <div class="card-illust" style="background:linear-gradient(135deg,#fce7f3,#fbcfe8)">
          <svg viewBox="0 0 24 24" fill="none" stroke="#a21caf" stroke-width="2"><path d="M12 3l7 3v5c0 4.6-2.8 8.3-7 10-4.2-1.7-7-5.4-7-10V6l7-3z"/><path d="M9 12l2 2 4-4" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
      </div>
      <div class="card-title">Tự động che thông tin</div>
      <div class="card-desc">Ẩn toàn bộ thông tin cá nhân trong văn bản Word trước khi công bố hoặc giao cho AI xử lý.</div>
      <div class="card-footer">Bảo mật · Không rời máy <span class="arrow">→</span></div>
    </button>

    <button class="card wide" data-name="đổi tên file" onclick="go('renamer')">
      <div class="card-top">
        <span class="badge badge-doc">Tài liệu</span>
        <div class="card-illust" style="background:linear-gradient(135deg,#ffedd5,#fed7aa)">
          <svg viewBox="0 0 24 24" fill="none" stroke="#c2410c" stroke-width="2"><path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
        </div>
      </div>
      <div class="card-title">Tự động đổi tên file</div>
      <div class="card-desc">Đổi tên hàng loạt, chuẩn hóa Unicode, đánh số bút lục hoặc tài liệu.</div>
      <div class="card-footer">Tài liệu · Hàng loạt <span class="arrow">→</span></div>
    </button>

    <button class="card wide" data-name="chính tả" onclick="go('spell_checker')">
      <div class="card-top">
        <span class="badge badge-doc">Tài liệu</span>
        <div class="card-illust" style="background:linear-gradient(135deg,#dcfce7,#bbf7d0)">
          <svg viewBox="0 0 24 24" fill="none" stroke="#15803d" stroke-width="2"><path d="M4 17l4 4L20 8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
      </div>
      <div class="card-title">Rà soát chính tả Word</div>
      <div class="card-desc">Phát hiện lỗi chính tả và xuất bản Word tô vàng hoặc bản đã sửa.</div>
      <div class="card-footer">Tài liệu · Không AI <span class="arrow">→</span></div>
    </button>

    <button class="card wide" data-name="nhận dạng ocr pdf ảnh" onclick="go('ocr')">
      <div class="card-top">
        <span class="badge badge-doc">Tài liệu</span>
        <div class="card-illust" style="background:linear-gradient(135deg,#e0f2fe,#bae6fd)">
          <svg viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35M8 11h6M11 8v6" stroke-linecap="round"/></svg>
        </div>
      </div>
      <div class="card-title">Nhận dạng chữ PDF, ảnh</div>
      <div class="card-desc">Trích xuất chữ từ PDF và ảnh, xuất Word, Markdown hoặc TXT.</div>
      <div class="card-footer">Tài liệu · Tesseract <span class="arrow">→</span></div>
    </button>
  </section>

  <!-- PRIVACY NOTICE -->
  <div class="privacy-notice">
    <div class="privacy-icon">✓</div>
    <div>
      <strong>Xử lý hoàn toàn cục bộ</strong>
      <span>Dữ liệu chỉ được xử lý trên máy tính này, không gửi lên mạng.</span>
    </div>
  </div>

  <!-- FOOTER -->
  <div class="foot">
    Phát triển bởi: <strong>Nguyễn Khắc Tú - Viện KSND khu vực 5 - Bắc Ninh</strong>
    <img id="footer-logo" src="__LOGO_DATA__" alt="Logo ngành Kiểm sát">
  </div>
</div>

<script>
document.getElementById('footer-logo').src = document.querySelector('.brand-logo').src;

function go(id){
  if(window.pywebview && window.pywebview.api){
    try{ window.pywebview.api.launch(id).then(function(r){ if(!r.ok) alert(r.message); }); }
    catch(e){ alert('Không thể mở công cụ: '+e); }
  } else {
    alert('Đây là bản demo giao diện. Công cụ "'+id+'" chỉ mở được trong ứng dụng offline thật.');
  }
}

function filterTools(){
  var q = document.getElementById('searchInput').value.toLowerCase().trim();
  var cards = document.querySelectorAll('.card');
  var anyInCalc = false, anyInDoc = false;
  cards.forEach(function(card){
    var name = (card.getAttribute('data-name')||'').toLowerCase();
    var match = !q || name.indexOf(q) !== -1;
    card.style.display = match ? '' : 'none';
    var inCalc = card.closest('.calc-grid');
    if(match && inCalc) anyInCalc = true;
    if(match && !inCalc) anyInDoc = true;
  });
  var calcSec = document.querySelector('.calc-grid'), docSec = document.querySelector('.doc-grid');
  var secTitles = document.querySelectorAll('.section-title');
  var showCalc = anyInCalc, showDoc = anyInDoc;
  // gộp khi tìm kiếm
  if(!showCalc) calcSec.style.display = 'none'; else calcSec.style.display = '';
  if(!showDoc) docSec.style.display = 'none'; else docSec.style.display = '';
  secTitles.forEach(function(t){
    var isCalc = t.getAttribute('data-section') === 'calc';
    t.style.display = (isCalc ? showCalc : showDoc) ? '' : 'none';
  });
}
</script>
</body>
</html>
</｜DSML｜>
<task_progress>
- [x] Tạo file DesktopOffline/launcher_demo.html với giao diện mới
- [ ] Người dùng xem trước và duyệt
- [ ] Tích hợp vào main.py (LAUNCHER_HTML) nếu duyệt
- [ ] Build lại bản offline
</task_progress>
</write_to_file>"""


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
