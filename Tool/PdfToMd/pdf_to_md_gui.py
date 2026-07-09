# -*- coding: utf-8 -*-
"""
PdfToMd GUI - Công cụ chuyển đổi PDF/Ảnh sang Markdown (Web-based GUI)
======================================================================
Flask backend + HTML/JS frontend tích hợp trong 1 file Python.
Sử dụng: python pdf_to_md_gui.py
"""
import os
import sys
import subprocess
import importlib

# ============================================================
# AUTO-INSTALL THƯ VIỆN THIẾU (dùng module chung auto_install.py)
# ============================================================
_TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT_DIR = os.path.dirname(_TOOL_DIR)  # Tool/
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)
from auto_install import check_and_install

check_and_install({
    "flask": "flask",
    "pypdf": "pypdf",
    "aiohttp": "aiohttp",
    "nest_asyncio": "nest-asyncio",
    "docx": "python-docx",
})

import json
import time
import threading
import webbrowser
import ctypes
import socket
from ctypes import wintypes
from pathlib import Path
from flask import Flask, request, jsonify

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from pdf_to_md import convert_file, read_pdf_with_pypdf, get_pdf_info, SUPPORTED_EXTENSIONS
    ENGINE_AVAILABLE = True
except ImportError as e:
    ENGINE_AVAILABLE = False
    print(f"[WARNING] Không thể import pdf_to_md: {e}. Dùng engine dự phòng.")

# ============================================================
# FIND FREE PORT (tránh xung đột với FileRenamer:5789, DocxToMd:5788)
# ============================================================
def find_free_port(start_port=5790, max_attempts=100):
    """Tìm cổng trống bắt đầu từ start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    # Fallback: để Flask tự chọn
    return 0

def browse_folder_windows(title="Chọn thư mục"):
    BIF_RETURNONLYFSDIRS = 0x0001
    BIF_NEWDIALOGSTYLE = 0x0040
    BIF_EDITBOX = 0x0010
    class BROWSEINFO(ctypes.Structure):
        _fields_ = [
            ("hwndOwner", wintypes.HWND),
            ("pidlRoot", ctypes.c_void_p),
            ("pszDisplayName", ctypes.c_wchar_p),
            ("lpszTitle", ctypes.c_wchar_p),
            ("ulFlags", wintypes.UINT),
            ("lpfn", ctypes.c_void_p),
            ("lParam", ctypes.c_void_p),
            ("iImage", ctypes.c_int),
        ]
    SHBrowseForFolderW = ctypes.windll.shell32.SHBrowseForFolderW
    SHBrowseForFolderW.restype = ctypes.c_void_p
    SHBrowseForFolderW.argtypes = [ctypes.POINTER(BROWSEINFO)]
    SHGetPathFromIDListW = ctypes.windll.shell32.SHGetPathFromIDListW
    SHGetPathFromIDListW.restype = wintypes.BOOL
    SHGetPathFromIDListW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    CoInitialize = ctypes.windll.ole32.CoInitialize
    CoInitialize.restype = wintypes.HRESULT
    CoInitialize.argtypes = [ctypes.c_void_p]
    CoUninitialize = ctypes.windll.ole32.CoUninitialize

    # Khởi tạo COM, kiểm tra lỗi
    hr = CoInitialize(None)
    if hr < 0 and hr != 0x00000001:  # S_FALSE (đã init) hoặc S_OK (0)
        print(f"[ERROR] Không thể khởi tạo COM (HRESULT: 0x{hr & 0xFFFFFFFF:08X})")
        return ""

    path_buffer = ctypes.create_unicode_buffer(260)
    bi = BROWSEINFO()
    bi.hwndOwner = 0
    bi.lpszTitle = title
    bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE | BIF_EDITBOX
    pidl = SHBrowseForFolderW(ctypes.byref(bi))
    result = ""
    if pidl and SHGetPathFromIDListW(pidl, path_buffer):
        result = path_buffer.value
    CoUninitialize()
    return result

SUPPORTED_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif", ".webp"}

app = Flask(__name__, static_folder=None)

def scan_directory(root_dir, force=False):
    if not os.path.isdir(root_dir):
        return []
    results = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext not in SUPPORTED_EXTS:
                continue
            source_path = os.path.join(dirpath, filename)
            stem = Path(filename).stem
            md_path = os.path.join(dirpath, stem + ".md")
            if not force and os.path.exists(md_path):
                continue
            results.append((ext, source_path, md_path))
    return results

def convert_file_local(file_path, api_key, workers=3, harmonize=False):
    if ENGINE_AVAILABLE:
        import pdf_to_md as engine
        old_key = engine.GEMINI_API_KEY
        engine.GEMINI_API_KEY = api_key
        try:
            ok, out_path = convert_file(file_path, api_key=api_key, workers=workers, harmonize=harmonize)
            return ok, out_path
        finally:
            engine.GEMINI_API_KEY = old_key
    else:
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            text = read_pdf_with_pypdf(file_path)
            if text:
                md_path = str(Path(file_path).parent / (Path(file_path).stem + ".md"))
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(text)
                return True, md_path
        return False, None

# ============================================================
# LAUNCHER HTML TEMPLATE (Route: /)
# ============================================================
LAUNCHER_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PdfToMd - Công cụ chuyển đổi PDF/Ảnh sang Markdown</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        :root {
            --sky: #5da9d9; --sky-light: #a8d4f0; --sky-dark: #1e5a8a;
            --bronze: #c9952e; --bronze-light: #e8c675;
            --plum: #7b2d42; --plum-dark: #5a1f30; --plum-light: #a84560;
            --green: #2e7d32; --green-light: #e8f5e9;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Be Vietnam Pro', Arial, sans-serif;
            background: linear-gradient(135deg, #f0f7fc 0%, #faf5f0 50%, #fefcf5 100%);
            color: #333; min-height: 100vh; overflow-x: hidden;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }
        .header {
            background: linear-gradient(135deg, var(--sky-dark), var(--plum-dark));
            border-bottom: 3px solid var(--bronze);
            padding: 18px 28px; display: flex; align-items: center; gap: 14px;
            flex-wrap: wrap; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            position: fixed; top: 0; left: 0; right: 0; z-index: 100;
        }
        .header-icon {
            width: 48px; height: 48px;
            background: linear-gradient(135deg, var(--bronze), #e8a830);
            border-radius: 12px; display: flex; align-items: center; justify-content: center;
            font-size: 22px; color: #fff;
            box-shadow: 0 4px 12px rgba(201,149,46,0.3); flex-shrink: 0;
        }
        .header-title {
            font-size: clamp(18px, 2.5vw, 26px); font-weight: 800; color: #fff;
            text-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .header-title span { color: var(--bronze-light); }
        .header-sub {
            font-size: 12px; color: rgba(255,255,255,0.7);
            font-weight: 600; letter-spacing: 2px;
            text-transform: uppercase; margin-top: 2px;
        }
        .main-content { max-width: 800px; margin: 120px auto 40px; padding: 20px; text-align: center; }
        .launch-card {
            background: #fff; border-radius: 20px; padding: 50px 40px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.1);
            border: 1px solid rgba(93,169,217,0.15);
        }
        .launch-card h1 {
            font-size: 28px; color: var(--sky-dark); margin-bottom: 12px;
        }
        .launch-card p {
            font-size: 16px; color: #666; line-height: 1.7; margin-bottom: 30px;
        }
        .btn-launch {
            display: inline-flex; align-items: center; gap: 14px;
            padding: 20px 56px; font-size: 22px; font-weight: 700;
            font-family: inherit; color: #fff;
            background: linear-gradient(135deg, var(--green), #43a047);
            border: none; border-radius: 16px; cursor: pointer;
            box-shadow: 0 6px 24px rgba(46,125,50,0.4);
            transition: all 0.3s ease; letter-spacing: 1px;
            text-decoration: none;
        }
        .btn-launch:hover { transform: translateY(-4px); box-shadow: 0 12px 36px rgba(46,125,50,0.5); }
        .btn-launch:active { transform: translateY(0); }
        .btn-launch i { font-size: 28px; }
        .features {
            display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 36px; text-align: left;
        }
        .feature-item {
            background: #f8fafc; border: 1px solid #e8ecf0; border-radius: 12px;
            padding: 16px 20px; display: flex; align-items: flex-start; gap: 12px;
            font-size: 14px; color: #555;
        }
        .feature-item i { color: var(--bronze); font-size: 20px; margin-top: 2px; flex-shrink: 0; }
        .feature-item strong { color: #333; display: block; margin-bottom: 4px; }
        .dev-info {
            margin-top: 24px; font-size: 13px; color: #999;
        }
        .dev-info i { color: var(--bronze); margin: 0 4px; }
        @media (max-width: 600px) {
            .launch-card { padding: 30px 20px; }
            .btn-launch { padding: 16px 32px; font-size: 18px; width: 100%; justify-content: center; }
            .features { grid-template-columns: 1fr; }
            .header { padding: 12px 14px; }
            .main-content { margin-top: 100px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-icon"><i class="fas fa-file-pdf"></i></div>
        <div>
            <div class="header-title">Công cụ <span>chuyển đổi PDF/Ảnh</span> sang Markdown</div>
            <div class="header-sub"><i class="fas fa-robot"></i> Gemini OCR + pypdf — Hàng loạt, tự động</div>
        </div>
    </div>

    <div class="main-content">
        <div class="launch-card">
            <h1><i class="fas fa-rocket" style="color:var(--bronze);"></i> Sẵn sàng chuyển đổi!</h1>
            <p>
                Công cụ <strong>PdfToMd</strong> giúp bạn chuyển đổi hàng loạt file PDF và ảnh
                (<strong>.pdf, .jpg, .png, .tiff, .bmp, .gif, .webp</strong>) sang định dạng
                <strong>Markdown (.md)</strong> một cách nhanh chóng và tự động.
            </p>
            <a href="/app" class="btn-launch">
                <i class="fas fa-play-circle"></i>
                KHỞI CHẠY CÔNG CỤ
            </a>

            <div class="features">
                <div class="feature-item">
                    <i class="fas fa-folder-open"></i>
                    <span><strong>Chọn thư mục cha</strong>Tự động quét toàn bộ thư mục con</span>
                </div>
                <div class="feature-item">
                    <i class="fas fa-list-check"></i>
                    <span><strong>Xem trước danh sách</strong>Hiển thị file theo cây thư mục</span>
                </div>
                <div class="feature-item">
                    <i class="fas fa-check-square"></i>
                    <span><strong>Tích chọn linh hoạt</strong>Chọn/bỏ chọn từng file hoặc cả thư mục</span>
                </div>
                <div class="feature-item">
                    <i class="fas fa-file-code"></i>
                    <span><strong>Kết quả .md</strong>File .md tạo bên cạnh file gốc</span>
                </div>
            </div>
        </div>
        <div class="dev-info">
            <i class="fas fa-cog"></i> Engine: Gemini 2.5 Flash API + pypdf |
            <i class="fas fa-user"></i> Nguyễn Khắc Tú |
            <i class="fas fa-building"></i> Viện KSND khu vực 5 - Bắc Ninh |
            <i class="fas fa-tools"></i> v1.0
        </div>
    </div>
</body>
</html>
'''

# ============================================================
# APP HTML TEMPLATE (Route: /app) - Giao diện chuyển đổi thực tế
# ============================================================
APP_TEMPLATE = r'''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PdfToMd - Chuyển đổi PDF/Ảnh sang Markdown</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        :root {
            --sky: #5da9d9; --sky-light: #a8d4f0; --sky-dark: #1e5a8a;
            --bronze: #c9952e; --bronze-light: #e8c675;
            --plum: #7b2d42; --plum-dark: #5a1f30; --plum-light: #a84560;
            --green: #2e7d32; --green-light: #e8f5e9;
            --red: #c62828; --red-light: #ffebee;
            --orange: #e65100;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Be Vietnam Pro', Arial, sans-serif;
            background: #f5f7fa; color: #333; min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, var(--sky-dark), var(--plum-dark));
            border-bottom: 3px solid var(--bronze);
            padding: 12px 24px; display: flex; align-items: center; gap: 12px;
            flex-wrap: wrap; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            position: sticky; top: 0; z-index: 100;
        }
        .header-icon {
            width: 40px; height: 40px;
            background: linear-gradient(135deg, var(--bronze), #e8a830);
            border-radius: 10px; display: flex; align-items: center; justify-content: center;
            font-size: 18px; color: #fff; flex-shrink: 0;
        }
        .header-title { font-size: 18px; font-weight: 800; color: #fff; }
        .header-title span { color: var(--bronze-light); }
        .header-back {
            margin-left: auto; color: #fff; text-decoration: none;
            font-size: 14px; font-weight: 600; opacity: 0.8; transition: opacity 0.2s;
        }
        .header-back:hover { opacity: 1; }
        .container { max-width: 960px; margin: 0 auto; padding: 24px 16px; }

        /* Cards */
        .card {
            background: #fff; border-radius: 14px; padding: 24px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 20px;
            border: 1px solid #e8ecf0;
        }
        .card-title {
            font-size: 17px; font-weight: 700; color: var(--sky-dark);
            margin-bottom: 16px; display: flex; align-items: center; gap: 10px;
        }
        .card-title i { color: var(--bronze); }

        /* API Key Section */
        .key-row {
            display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
        }
        .key-input {
            flex: 1; min-width: 250px; padding: 10px 14px;
            border: 2px solid #dde; border-radius: 8px; font-size: 14px;
            font-family: inherit; transition: border-color 0.2s;
        }
        .key-input:focus { outline: none; border-color: var(--sky); }
        .btn { 
            padding: 10px 20px; border: none; border-radius: 8px;
            font-size: 14px; font-weight: 600; font-family: inherit;
            cursor: pointer; transition: all 0.2s; white-space: nowrap;
        }
        .btn-primary { background: var(--sky-dark); color: #fff; }
        .btn-primary:hover { background: #174a72; }
        .btn-success { background: var(--green); color: #fff; }
        .btn-success:hover { background: #256b29; }
        .btn-warning { background: var(--orange); color: #fff; }
        .btn-warning:hover { background: #bf4500; }
        .btn-outline { background: #fff; color: var(--sky-dark); border: 2px solid var(--sky-dark); }
        .btn-outline:hover { background: #f0f7fc; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .key-status {
            font-size: 13px; margin-top: 8px; padding: 8px 12px;
            border-radius: 6px; display: inline-block;
        }
        .key-ok { background: var(--green-light); color: var(--green); }
        .key-missing { background: #fff3e0; color: var(--orange); }
        .key-error { background: var(--red-light); color: var(--red); }

        /* Folder Section */
        .folder-row {
            display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
        }
        .folder-input {
            flex: 1; min-width: 250px; padding: 10px 14px;
            border: 2px solid #dde; border-radius: 8px; font-size: 14px;
            font-family: inherit; background: #fafafa;
        }
        .folder-input:focus { outline: none; border-color: var(--sky); }

        /* Scan Options */
        .scan-options { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; margin-top: 12px; }
        .scan-options label { font-size: 13px; color: #666; display: flex; align-items: center; gap: 6px; cursor: pointer; }
        .scan-options input[type="checkbox"] { width: 16px; height: 16px; cursor: pointer; }

        /* File List */
        .file-summary {
            font-size: 14px; color: #666; margin-bottom: 12px;
            display: flex; gap: 16px; align-items: center; flex-wrap: wrap;
        }
        .file-summary strong { color: #333; }
        .file-tree { max-height: 400px; overflow-y: auto; }
        .folder-group { margin-bottom: 8px; }
        .folder-header {
            padding: 8px 12px; background: #f0f4f8; border-radius: 6px;
            font-weight: 700; font-size: 13px; color: var(--sky-dark);
            cursor: pointer; display: flex; align-items: center; gap: 8px;
            user-select: none; transition: background 0.15s;
        }
        .folder-header:hover { background: #e4ecf4; }
        .folder-header i { font-size: 12px; transition: transform 0.2s; }
        .folder-header.collapsed i { transform: rotate(-90deg); }
        .folder-files { margin-left: 16px; }
        .folder-files.collapsed { display: none; }
        .file-item {
            display: flex; align-items: center; gap: 8px; padding: 6px 10px;
            border-radius: 4px; font-size: 13px; cursor: pointer; transition: background 0.1s;
        }
        .file-item:hover { background: #f8fafc; }
        .file-item input[type="checkbox"] { width: 15px; height: 15px; cursor: pointer; flex-shrink: 0; }
        .file-item .file-icon { color: var(--sky); font-size: 14px; width: 18px; text-align: center; flex-shrink: 0; }
        .file-item .file-name { flex: 1; word-break: break-all; }
        .file-item .file-size { font-size: 11px; color: #999; flex-shrink: 0; }
        .file-item .file-md-exists { font-size: 11px; color: var(--green); flex-shrink: 0; }
        .file-item .file-md-exists::before { content: '✓ '; }
        .select-all-row {
            padding: 8px 12px; border-bottom: 1px solid #eee; margin-bottom: 8px;
            display: flex; gap: 16px; align-items: center;
        }
        .select-all-row label { font-size: 13px; font-weight: 600; color: #555; cursor: pointer; display: flex; align-items: center; gap: 6px; }

        /* Convert */
        .convert-section { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        .btn-convert {
            padding: 14px 36px; font-size: 16px; font-weight: 700;
        }

        /* Progress */
        .progress-bar-outer {
            background: #e0e0e0; border-radius: 8px; height: 20px; overflow: hidden; margin: 12px 0;
        }
        .progress-bar-inner {
            height: 100%; background: linear-gradient(90deg, var(--sky), var(--green));
            border-radius: 8px; transition: width 0.3s; width: 0%;
            display: flex; align-items: center; justify-content: center;
            font-size: 11px; color: #fff; font-weight: 700;
        }
        .progress-text { font-size: 13px; color: #666; text-align: center; }

        /* Results */
        .result-item {
            display: flex; align-items: center; gap: 10px; padding: 10px 12px;
            border-radius: 6px; margin-bottom: 6px; font-size: 13px;
        }
        .result-ok { background: var(--green-light); }
        .result-fail { background: var(--red-light); }
        .result-icon { font-size: 16px; flex-shrink: 0; }
        .result-icon.ok { color: var(--green); }
        .result-icon.fail { color: var(--red); }
        .result-file { flex: 1; word-break: break-all; }
        .result-info { font-size: 12px; color: #666; flex-shrink: 0; white-space: nowrap; }

        .empty-state {
            text-align: center; padding: 40px 20px; color: #aaa;
        }
        .empty-state i { font-size: 48px; margin-bottom: 12px; display: block; }
        .empty-state p { font-size: 15px; }

        .spinner {
            display: inline-block; width: 16px; height: 16px;
            border: 2px solid #ccc; border-top-color: var(--sky-dark);
            border-radius: 50%; animation: spin 0.6s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        .alert-box {
            padding: 12px 16px; border-radius: 8px; margin-top: 8px;
            font-size: 13px; line-height: 1.5;
        }
        .alert-box.info { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
        .alert-box.error { background: var(--red-light); color: var(--red); border: 1px solid #ef9a9a; }

        @media (max-width: 600px) {
            .header { padding: 10px 14px; }
            .header-title { font-size: 15px; }
            .container { padding: 12px 8px; }
            .card { padding: 16px; }
            .folder-row, .key-row { flex-direction: column; }
            .btn { width: 100%; text-align: center; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-icon"><i class="fas fa-file-pdf"></i></div>
        <div class="header-title">PdfToMd <span>Chuyển đổi</span></div>
        <a href="/" class="header-back"><i class="fas fa-home"></i> Trang chủ</a>
    </div>

    <div class="container">
        <!-- API Key Card -->
        <div class="card" id="keyCard">
            <div class="card-title"><i class="fas fa-key"></i> Bước 1: Nhập Gemini API Key</div>
            <div class="key-row">
                <input type="password" id="apiKeyInput" class="key-input" placeholder="Nhập Gemini API Key (lấy tại Google AI Studio)...">
                <button class="btn btn-primary" onclick="saveApiKey()"><i class="fas fa-save"></i> Lưu API Key</button>
                <button class="btn btn-outline" onclick="checkApiKey()"><i class="fas fa-search"></i> Kiểm tra</button>
            </div>
            <div id="keyStatus"></div>
        </div>

        <!-- Folder Card -->
        <div class="card">
            <div class="card-title"><i class="fas fa-folder-open"></i> Bước 2: Chọn thư mục cha</div>
            <div class="folder-row">
                <input type="text" id="folderPath" class="folder-input" placeholder="Đường dẫn thư mục chứa file PDF/Ảnh...">
                <button class="btn btn-outline" onclick="browseFolder()"><i class="fas fa-folder"></i> Chọn thư mục</button>
            </div>
            <div id="folderAlert"></div>
            <div class="scan-options">
                <label><input type="checkbox" id="forceScan"> Quét cả file đã có .md</label>
                <button class="btn btn-primary" onclick="scanFolder()"><i class="fas fa-search"></i> Quét ngay</button>
            </div>
        </div>

        <!-- File List Card -->
        <div class="card" id="fileListCard" style="display:none;">
            <div class="card-title"><i class="fas fa-list"></i> Bước 3: Chọn file cần chuyển đổi</div>
            <div class="file-summary">
                <span>Tổng: <strong id="totalFiles">0</strong> file</span>
                <span>Đã chọn: <strong id="selectedCount">0</strong> file</span>
            </div>
            <div class="select-all-row">
                <label><input type="checkbox" id="selectAll" onchange="toggleSelectAll()"> Chọn tất cả</label>
                <label><input type="checkbox" id="selectMissing" onchange="toggleSelectMissing()" checked> Chỉ chọn file chưa có .md</label>
            </div>
            <div class="file-tree" id="fileTree"></div>

            <!-- Convert Button -->
            <div class="convert-section" style="margin-top:16px;">
                <button class="btn btn-success btn-convert" id="btnConvert" onclick="startConvert()" disabled>
                    <i class="fas fa-play"></i> Thực thi chuyển đổi
                </button>
                <span style="font-size:13px;color:#666;">Số luồng: 
                    <select id="workers" style="padding:4px 8px;border-radius:4px;border:1px solid #ddd;font-family:inherit;">
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3" selected>3</option>
                        <option value="5">5</option>
                    </select>
                </span>
            </div>

            <!-- Progress -->
            <div id="progressSection" style="display:none; margin-top:16px;">
                <div class="progress-bar-outer">
                    <div class="progress-bar-inner" id="progressBar"></div>
                </div>
                <div class="progress-text" id="progressText"></div>
            </div>

            <!-- Results -->
            <div id="resultsContainer" style="margin-top:16px;"></div>
        </div>
    </div>

    <script>
        // ============ STATE ============
        var allFiles = [];
        var folderChecks = {};

        // ============ HELPER: Show message ============
        function showAlert(elId, msg, type) {
            var el = document.getElementById(elId);
            if (!el) return;
            type = type || 'info';
            el.innerHTML = '<div class="alert-box ' + type + '"><i class="fas fa-' + 
                (type === 'error' ? 'exclamation-circle' : 'info-circle') + '"></i> ' + msg + '</div>';
        }
        function clearAlert(elId) {
            var el = document.getElementById(elId);
            if (el) el.innerHTML = '';
        }

        // ============ ON LOAD ============
        window.onload = function() {
            checkApiKey();
        };

        // ============ API KEY ============
        function checkApiKey() {
            var statusEl = document.getElementById('keyStatus');
            statusEl.innerHTML = '<span class="spinner"></span> Đang kiểm tra...';
            fetch('/api/check-key')
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.has_key) {
                        document.getElementById('apiKeyInput').value = data.key_masked;
                        statusEl.innerHTML = '<div class="key-status key-ok"><i class="fas fa-check-circle"></i> Đã có API Key: ' + data.key_masked + '</div>';
                    } else {
                        statusEl.innerHTML = '<div class="key-status key-missing"><i class="fas fa-exclamation-triangle"></i> Chưa có API Key. Vui lòng nhập key từ Google AI Studio.</div>';
                    }
                })
                .catch(function(e) {
                    statusEl.innerHTML = '<div class="key-status key-error">Lỗi kết nối máy chủ: ' + e + '</div>';
                });
        }

        function saveApiKey() {
            var key = document.getElementById('apiKeyInput').value.trim();
            if (!key) { showAlert('keyStatus', 'Vui lòng nhập API Key!', 'error'); return; }
            var statusEl = document.getElementById('keyStatus');
            statusEl.innerHTML = '<span class="spinner"></span> Đang lưu...';
            fetch('/api/save-key', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({api_key: key})
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.ok) {
                    statusEl.innerHTML = '<div class="key-status key-ok"><i class="fas fa-check-circle"></i> Đã lưu API Key: ' + data.key_masked + '</div>';
                    document.getElementById('apiKeyInput').value = data.key_masked;
                } else {
                    statusEl.innerHTML = '<div class="key-status key-error">Lỗi: ' + (data.error || 'Không thể lưu') + '</div>';
                }
            })
            .catch(function(e) {
                statusEl.innerHTML = '<div class="key-status key-error">Lỗi kết nối khi lưu API Key: ' + e + '</div>';
            });
        }

        // ============ FOLDER ============
        function browseFolder() {
            clearAlert('folderAlert');
            var btn = document.querySelector('.btn-outline');  // Nút "Chọn thư mục"
            var origText = btn ? btn.innerHTML : '';
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner"></span> Đang mở...';
            }
            fetch('/api/browse-folder')
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (btn) { btn.disabled = false; btn.innerHTML = origText; }
                    if (data.path) {
                        document.getElementById('folderPath').value = data.path;
                        clearAlert('folderAlert');
                    } else if (data.error) {
                        showAlert('folderAlert', data.error + '<br><small>Bạn vẫn có thể dán đường dẫn thủ công vào ô bên trên và bấm "Quét ngay".</small>', 'error');
                    } else {
                        showAlert('folderAlert', 'Bạn đã hủy chọn thư mục, hoặc hộp thoại không khả dụng.<br><small>Vui lòng dán đường dẫn thư mục thủ công vào ô bên trên và bấm "Quét ngay".</small>', 'info');
                    }
                })
                .catch(function(e) {
                    if (btn) { btn.disabled = false; btn.innerHTML = origText; }
                    showAlert('folderAlert', 'Không thể mở hộp thoại chọn thư mục (lỗi: ' + e + ').<br><small>Vui lòng dán đường dẫn thư mục thủ công vào ô bên trên và bấm "Quét ngay".</small>', 'error');
                });
        }

        function scanFolder() {
            var folderPath = document.getElementById('folderPath').value.trim();
            if (!folderPath) { alert('Vui lòng nhập hoặc chọn thư mục!'); return; }
            var force = document.getElementById('forceScan').checked;

            var treeEl = document.getElementById('fileTree');
            treeEl.innerHTML = '<div class="empty-state"><span class="spinner"></span><p>Đang quét thư mục...</p></div>';
            document.getElementById('fileListCard').style.display = 'block';
            document.getElementById('btnConvert').disabled = true;
            document.getElementById('progressSection').style.display = 'none';
            document.getElementById('resultsContainer').innerHTML = '';
            clearAlert('folderAlert');

            fetch('/api/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: folderPath, force: force})
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.error) {
                    treeEl.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle" style="color:#c62828;"></i><p>' + data.error + '</p></div>';
                    return;
                }
                allFiles = data.files || [];
                document.getElementById('totalFiles').textContent = allFiles.length;
                renderFileTree();
            })
            .catch(function(e) {
                treeEl.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle" style="color:#c62828;"></i><p>Lỗi kết nối: ' + e + '</p></div>';
            });
        }

        // ============ FILE TREE ============
        function renderFileTree() {
            var treeEl = document.getElementById('fileTree');
            if (allFiles.length === 0) {
                treeEl.innerHTML = '<div class="empty-state"><i class="fas fa-inbox"></i><p>Không tìm thấy file PDF/Ảnh nào trong thư mục này.</p></div>';
                document.getElementById('selectedCount').textContent = '0';
                document.getElementById('btnConvert').disabled = true;
                return;
            }

            // Group by folder
            var groups = {};
            allFiles.forEach(function(f, i) {
                var folder = f.folder || '(Thư mục gốc)';
                if (!groups[folder]) groups[folder] = [];
                f._idx = i;
                groups[folder].push(f);
            });

            // Init folder check states
            Object.keys(groups).forEach(function(folder) {
                if (!(folder in folderChecks)) folderChecks[folder] = true;
            });

            var html = '';
            var folderNames = Object.keys(groups).sort(function(a, b) {
                if (a === '(Thư mục gốc)') return -1;
                if (b === '(Thư mục gốc)') return 1;
                return a.localeCompare(b);
            });

            folderNames.forEach(function(folder) {
                var files = groups[folder];
                var checked = folderChecks[folder] !== false;
                var allInFolderChecked = files.every(function(f) { return f._checked !== false; });
                var someChecked = files.some(function(f) { return f._checked !== false; });

                html += '<div class="folder-group">';
                html += '<div class="folder-header" onclick="toggleFolder(this)">';
                html += '<i class="fas fa-chevron-down"></i>';
                html += '<input type="checkbox" onchange="toggleFolderCheck(\'' + escHtml(folder) + '\', this.checked)" ' + (allInFolderChecked ? 'checked' : (someChecked ? '' : '')) + ' onclick="event.stopPropagation()">';
                html += '<i class="fas fa-folder" style="color:var(--bronze);"></i>';
                html += escHtml(folder) + ' <span style="font-weight:400;color:#999;">(' + files.length + ' file)</span>';
                html += '</div>';
                html += '<div class="folder-files">';
                files.forEach(function(f) {
                    var isChecked = f._checked !== false;
                    var iconExt = getFileIcon(f.ext);
                    html += '<div class="file-item" onclick="toggleFileCheck(' + f._idx + ', this)">';
                    html += '<input type="checkbox" ' + (isChecked ? 'checked' : '') + ' onchange="updateFileCheck(' + f._idx + ', this.checked)" onclick="event.stopPropagation()">';
                    html += '<span class="file-icon">' + iconExt + '</span>';
                    html += '<span class="file-name">' + escHtml(f.filename) + '</span>';
                    if (f.md_exists) {
                        html += '<span class="file-md-exists">đã có .md</span>';
                    }
                    html += '<span class="file-size">' + f.size_mb + ' MB</span>';
                    html += '</div>';
                });
                html += '</div></div>';
            });

            treeEl.innerHTML = html;
            updateSelectionCount();
        }

        function escHtml(str) {
            var d = document.createElement('div');
            d.textContent = str;
            return d.innerHTML;
        }

        function getFileIcon(ext) {
            var map = {'.pdf': '📄', '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.tiff': '🖼️', '.tif': '🖼️', '.bmp': '🖼️', '.gif': '🖼️', '.webp': '🖼️'};
            return map[ext] || '📎';
        }

        function toggleFolder(header) {
            header.classList.toggle('collapsed');
            header.nextElementSibling.classList.toggle('collapsed');
        }

        function toggleFolderCheck(folder, checked) {
            folderChecks[folder] = checked;
            allFiles.forEach(function(f) {
                if (f.folder === folder || (folder === '(Thư mục gốc)' && f.folder === '(Thư mục gốc)')) {
                    f._checked = checked;
                }
            });
            renderFileTree();
        }

        function toggleFileCheck(idx, row) {
            var f = allFiles[idx];
            f._checked = !(f._checked !== false);
            updateFileCheck(idx, f._checked !== false);
        }

        function updateFileCheck(idx, checked) {
            allFiles[idx]._checked = checked;
            updateSelectionCount();
        }

        function toggleSelectAll() {
            var checked = document.getElementById('selectAll').checked;
            allFiles.forEach(function(f) { f._checked = checked; });
            Object.keys(folderChecks).forEach(function(k) { folderChecks[k] = checked; });
            renderFileTree();
        }

        function toggleSelectMissing() {
            var onlyMissing = document.getElementById('selectMissing').checked;
            if (onlyMissing) {
                allFiles.forEach(function(f) {
                    if (f.md_exists) f._checked = false;
                    else f._checked = true;
                });
            } else {
                allFiles.forEach(function(f) { f._checked = true; });
            }
            renderFileTree();
        }

        function updateSelectionCount() {
            var count = allFiles.filter(function(f) { return f._checked !== false; }).length;
            document.getElementById('selectedCount').textContent = count;
            document.getElementById('btnConvert').disabled = (count === 0);
        }

        // ============ CONVERT ============
        function startConvert() {
            var selected = allFiles.filter(function(f) { return f._checked !== false; });
            if (selected.length === 0) { alert('Vui lòng chọn ít nhất 1 file để chuyển đổi!'); return; }

            document.getElementById('progressSection').style.display = 'block';
            document.getElementById('btnConvert').disabled = true;
            document.getElementById('resultsContainer').innerHTML = '';
            var progressBar = document.getElementById('progressBar');
            var progressText = document.getElementById('progressText');
            progressBar.style.width = '0%';
            progressBar.textContent = '0%';
            progressText.textContent = 'Đang chuyển đổi...';

            var workers = parseInt(document.getElementById('workers').value) || 3;
            var total = selected.length;
            var done = 0;
            var resultsHtml = '';

            function updateProgress() {
                var pct = Math.round((done / total) * 100);
                progressBar.style.width = pct + '%';
                progressBar.textContent = pct + '%';
                progressText.textContent = 'Đã xử lý: ' + done + ' / ' + total + ' file';
            }

            function processNext() {
                if (selected.length === 0) return;
                var f = selected.shift();
                var filePath = f.source_path;

                // Get API key from saved file (the backend reads it)
                return fetch('/api/convert', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        file_path: filePath,
                        api_key: '__from_file__',
                        workers: 1,
                        harmonize: false
                    })
                })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    done++;
                    updateProgress();
                    if (data.ok) {
                        resultsHtml += '<div class="result-item result-ok">' +
                            '<span class="result-icon ok"><i class="fas fa-check-circle"></i></span>' +
                            '<span class="result-file">' + escHtml(f.filename) + '</span>' +
                            '<span class="result-info">→ ' + escHtml(data.md_name || '') + ' (' + data.chars + ' ký tự, ' + data.method + ')</span>' +
                            '</div>';
                    } else {
                        resultsHtml += '<div class="result-item result-fail">' +
                            '<span class="result-icon fail"><i class="fas fa-times-circle"></i></span>' +
                            '<span class="result-file">' + escHtml(f.filename) + '</span>' +
                            '<span class="result-info">Lỗi: ' + escHtml(data.error || 'Không rõ') + '</span>' +
                            '</div>';
                    }
                    document.getElementById('resultsContainer').innerHTML = resultsHtml;
                })
                .catch(function(e) {
                    done++;
                    updateProgress();
                    resultsHtml += '<div class="result-item result-fail">' +
                        '<span class="result-icon fail"><i class="fas fa-times-circle"></i></span>' +
                        '<span class="result-file">' + escHtml(f.filename) + '</span>' +
                        '<span class="result-info">Lỗi: ' + escHtml(String(e)) + '</span>' +
                        '</div>';
                    document.getElementById('resultsContainer').innerHTML = resultsHtml;
                })
                .then(function() {
                    if (selected.length > 0) {
                        return processNext();
                    } else {
                        progressText.textContent = 'Hoàn thành! Đã xử lý ' + done + ' / ' + total + ' file.';
                        document.getElementById('btnConvert').disabled = false;
                    }
                });
            }

            // Start processing with concurrency
            var batch = [];
            for (var i = 0; i < workers && selected.length > 0; i++) {
                batch.push(processNext());
            }
            Promise.all(batch).then(function() {
                if (done >= total) {
                    progressText.textContent = 'Hoàn thành! Đã xử lý ' + done + ' / ' + total + ' file.';
                    document.getElementById('btnConvert').disabled = false;
                }
            });
        }
    </script>
</body>
</html>
'''

# ============================================================
# FLASK ROUTES
# ============================================================

@app.route('/')
def index():
    return LAUNCHER_TEMPLATE

@app.route('/app')
def app_page():
    return APP_TEMPLATE

@app.route('/api/browse-folder')
def browse_folder_api():
    try:
        folder = browse_folder_windows('Chọn thư mục cha chứa file PDF/Ảnh')
        if folder:
            folder = os.path.normpath(folder)
            return jsonify({'path': folder})
        else:
            # Không có lỗi nhưng cũng không có kết quả (có thể user cancel hoặc COM lỗi)
            return jsonify({'path': '', 'error': 'Không thể mở hộp thoại chọn thư mục. Hãy thử dán đường dẫn thủ công.'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'path': '', 'error': f'Lỗi khi mở hộp thoại: {str(e)}. Hãy dán đường dẫn thủ công.'})

@app.route('/api/scan', methods=['POST'])
def scan_folder_api():
    data = request.get_json()
    folder_path = data.get('path', '').strip()
    force = data.get('force', False)

    if not folder_path:
        return jsonify({'error': 'Vui lòng nhập đường dẫn thư mục.'})
    if not os.path.isdir(folder_path):
        return jsonify({'error': f'Thư mục không tồn tại: {folder_path}'})

    try:
        files = scan_directory(folder_path, force=force)
        results = []
        for ext, source_path, md_path in files:
            filename = os.path.basename(source_path)
            rel_dir = os.path.relpath(os.path.dirname(source_path), folder_path)
            if rel_dir == '.':
                folder_display = '(Thư mục gốc)'
            else:
                folder_display = rel_dir
            md_exists = os.path.exists(md_path)
            size_mb = os.path.getsize(source_path) / 1048576 if os.path.exists(source_path) else 0
            results.append({
                'ext': ext,
                'source_path': source_path,
                'md_path': md_path,
                'filename': filename,
                'folder': folder_display,
                'md_exists': md_exists,
                'size_mb': round(size_mb, 2),
            })
        results.sort(key=lambda x: (x['folder'] != '(Thư mục gốc)', x['folder'], x['filename']))
        return jsonify({'path': os.path.abspath(folder_path), 'files': results, 'total': len(results)})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Lỗi khi quét thư mục: {str(e)}'})

@app.route('/api/convert', methods=['POST'])
def convert_single():
    data = request.get_json()
    file_path = data.get('file_path', '')
    api_key = data.get('api_key', '')
    workers = int(data.get('workers', 3))
    harmonize = data.get('harmonize', False)

    if not file_path or not os.path.isfile(file_path):
        return jsonify({'ok': False, 'error': 'File không tồn tại'})

    # If api_key is placeholder, read from file
    if not api_key or api_key == '__from_file__':
        api_key = read_api_key_from_file()

    if not api_key:
        return jsonify({'ok': False, 'error': 'Thiếu API Key. Vui lòng nhập API Key ở Bước 1.'})

    try:
        ok, out_path = convert_file_local(file_path, api_key, workers=workers, harmonize=harmonize)
        if ok and out_path:
            md_name = os.path.basename(out_path)
            chars = 0
            method = 'pypdf'
            if os.path.exists(out_path):
                with open(out_path, 'r', encoding='utf-8') as f:
                    chars = len(f.read())
            ext = Path(file_path).suffix.lower()
            if ext != '.pdf' or not read_pdf_with_pypdf(file_path):
                method = 'Gemini API'
            return jsonify({'ok': True, 'md_name': md_name, 'chars': chars, 'method': method})
        else:
            return jsonify({'ok': False, 'error': 'Không thể chuyển đổi file này'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)})

API_KEYS_FILE = os.path.join(SCRIPT_DIR, 'API keys.txt')

def read_api_key_from_file():
    try:
        if not os.path.exists(API_KEYS_FILE):
            return ''
        with open(API_KEYS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('gemini|'):
                    key = line.split('|', 1)[1].strip()
                    if key:
                        return key
        return ''
    except Exception as e:
        print(f"[WARNING] Lỗi đọc API key file: {e}")
        return ''

def write_api_key_to_file(api_key):
    try:
        lines = []
        if os.path.exists(API_KEYS_FILE):
            with open(API_KEYS_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith('gemini|'):
                lines[i] = f'gemini|{api_key}\n'
                found = True
                break
        if not found:
            lines.append(f'gemini|{api_key}\n')
        with open(API_KEYS_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"[ERROR] Lỗi ghi API key file: {e}")
        return False

@app.route('/api/check-key')
def check_api_key():
    key = read_api_key_from_file()
    if key:
        masked = key[:8] + '...' + key[-4:] if len(key) > 12 else '***'
        return jsonify({'has_key': True, 'key_masked': masked})
    return jsonify({'has_key': False, 'key_masked': ''})

@app.route('/api/save-key', methods=['POST'])
def save_api_key():
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    if not api_key:
        return jsonify({'ok': False, 'error': 'API Key không được để trống'})
    if write_api_key_to_file(api_key):
        masked = api_key[:8] + '...' + api_key[-4:] if len(api_key) > 12 else '***'
        return jsonify({'ok': True, 'message': 'Đã lưu API Key vào file API keys.txt', 'key_masked': masked})
    else:
        return jsonify({'ok': False, 'error': 'Không thể ghi file API keys.txt'})

def main():
    host = '127.0.0.1'
    port = find_free_port(start_port=5790)

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print("=" * 60)
    print("  PdfToMd GUI - Chuyen doi PDF/Anh sang Markdown")
    print("=" * 60)
    print(f"  Server dang chay tai: http://{host}:{port}")
    print(f"  Giao dien chuyen doi: http://{host}:{port}/app")
    print("  Nhan Ctrl+C de thoat.")
    print("=" * 60)

    def open_browser():
        webbrowser.open(f'http://{host}:{port}/app')

    threading.Timer(1.5, open_browser).start()

    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == '__main__':
    main()