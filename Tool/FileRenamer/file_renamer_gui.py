# -*- coding: utf-8 -*-
"""
File Renamer GUI - Công cụ đổi tên hàng loạt file (Web-based GUI)
=================================================================
Flask backend + HTML/JS frontend tích hợp trong 1 file Python.
Sử dụng: python file_renamer_gui.py
"""

import os
import sys

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
})

import json
import threading
import webbrowser
import ctypes
from ctypes import wintypes
from pathlib import Path

from flask import Flask, request, jsonify

# --------------- Import FileRenamer từ file_renamer.py ---------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from file_renamer import FileRenamer

# ============================================================
# NATIVE WINDOWS FOLDER BROWSER (thay thế tkinter)
# ============================================================
def browse_folder_windows(title="Chọn thư mục"):
    """Mở hộp thoại chọn thư mục native Windows, không phụ thuộc tkinter."""
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

    GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
    GetForegroundWindow.restype = wintypes.HWND
    GetForegroundWindow.argtypes = []

    CoInitialize(None)

    # Lấy handle cửa sổ đang active (trình duyệt) để dialog nổi lên trước
    owner_hwnd = GetForegroundWindow()

    path_buffer = ctypes.create_unicode_buffer(260)
    bi = BROWSEINFO()
    bi.hwndOwner = owner_hwnd or 0
    bi.lpszTitle = title
    bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE | BIF_EDITBOX

    pidl = SHBrowseForFolderW(ctypes.byref(bi))
    result = ""
    if pidl and SHGetPathFromIDListW(pidl, path_buffer):
        result = path_buffer.value

    CoUninitialize()
    return result

app = Flask(__name__, static_folder=None)
renamer = FileRenamer()

# ============================================================
# HTML TEMPLATE
# ============================================================
HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Renamer - Đổi tên hàng loạt file</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        :root {
            --sky: #5da9d9; --sky-light: #a8d4f0; --sky-dark: #1e5a8a;
            --bronze: #c9952e; --bronze-light: #e8c675;
            --plum: #7b2d42; --plum-dark: #5a1f30; --plum-light: #a84560;
            --green: #2e7d32; --green-light: #e8f5e9;
            --red: #c62828; --red-light: #ffebee;
            --gray-bg: #f5f5f5; --border: #e0e0e0;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Be Vietnam Pro', Arial, sans-serif;
            background: linear-gradient(135deg, #f0f7fc 0%, #faf5f0 50%, #fefcf5 100%);
            color: #333; min-height: 100vh; overflow-x: hidden;
        }
        .header {
            background: linear-gradient(135deg, var(--sky-dark), var(--plum-dark));
            border-bottom: 3px solid var(--bronze);
            padding: 14px 28px; display: flex; align-items: center; gap: 14px;
            flex-wrap: wrap; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            position: sticky; top: 0; z-index: 100;
        }
        .header-icon {
            width: 46px; height: 46px;
            background: linear-gradient(135deg, var(--bronze), #e8a830);
            border-radius: 12px; display: flex; align-items: center; justify-content: center;
            font-size: 20px; color: #fff;
            box-shadow: 0 4px 12px rgba(201,149,46,0.3); flex-shrink: 0;
        }
        .header-title {
            font-size: clamp(15px, 2vw, 20px); font-weight: 800; color: #fff;
            text-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .header-title span { color: var(--bronze-light); }
        .header-sub {
            font-size: 11px; color: rgba(255,255,255,0.7);
            font-weight: 600; letter-spacing: 1.5px;
            text-transform: uppercase; margin-top: 2px;
        }
        .main-content { max-width: 1150px; margin: 0 auto; padding: 28px 16px; }

        .step-card {
            background: #fff; border-radius: 16px; padding: 24px 28px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            border: 1px solid rgba(93,169,217,0.15); margin-bottom: 22px;
        }
        .step-card h2 {
            font-size: 19px; color: var(--sky-dark); margin-bottom: 14px;
            display: flex; align-items: center; gap: 10px;
        }
        .step-card h2 i { color: var(--bronze); }
        .step-num {
            display: inline-flex; align-items: center; justify-content: center;
            width: 30px; height: 30px;
            background: linear-gradient(135deg, var(--sky-dark), var(--plum-dark));
            color: #fff; border-radius: 50%; font-size: 14px; font-weight: 800; flex-shrink: 0;
        }

        .folder-select-row {
            display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
        }
        .folder-input {
            flex: 1; min-width: 260px; padding: 11px 14px;
            border: 2px solid var(--border); border-radius: 10px;
            font-size: 14px; font-family: inherit; background: var(--gray-bg); color: #333;
            transition: border-color 0.2s;
        }
        .folder-input:focus { outline: none; border-color: var(--sky); background: #fff; }
        .btn {
            display: inline-flex; align-items: center; gap: 7px;
            padding: 11px 22px; font-size: 14px; font-weight: 700;
            font-family: inherit; border: none; border-radius: 10px;
            cursor: pointer; transition: all 0.25s ease; white-space: nowrap;
        }
        .btn-primary {
            color: #fff; background: linear-gradient(135deg, var(--sky-dark), var(--plum-dark));
            box-shadow: 0 4px 14px rgba(30,90,138,0.3);
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(30,90,138,0.4); }
        .btn-outline { color: var(--sky-dark); background: #fff; border: 2px solid var(--sky); }
        .btn-outline:hover { background: #e8f2fa; }
        .btn-success {
            color: #fff; background: linear-gradient(135deg, var(--green), #388e3c);
            box-shadow: 0 4px 14px rgba(46,125,50,0.3);
        }
        .btn-success:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(46,125,50,0.4); }
        .btn-success:disabled { background: #aaa; cursor: not-allowed; box-shadow: none; transform: none; }
        .btn-browse {
            color: #fff; background: linear-gradient(135deg, var(--bronze), #e0a030);
            box-shadow: 0 4px 12px rgba(201,149,46,0.25);
        }
        .btn-browse:hover { transform: translateY(-2px); }

        .action-bar {
            display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
            padding: 14px 0; border-bottom: 1px solid var(--border); margin-bottom: 10px;
        }
        .action-bar .btn { font-size: 13px; padding: 8px 16px; }
        .action-bar .separator { width: 1px; height: 24px; background: var(--border); margin: 0 4px; }

        .stats-row {
            display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px;
        }
        .stat-badge {
            padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;
            display: inline-flex; align-items: center; gap: 6px;
        }
        .stat-badge.info { background: #e3f2fd; color: var(--sky-dark); }
        .stat-badge.success { background: var(--green-light); color: var(--green); }
        .stat-badge.warning { background: #fff8e1; color: #f57f17; }

        /* TREE VIEW */
        .tree-container { max-height: 55vh; overflow-y: auto; }
        .tree-folder {
            margin-bottom: 4px;
            border: 1px solid transparent;
            border-radius: 8px;
            transition: background 0.15s;
        }
        .tree-folder:hover { background: #fafafa; }
        .folder-header {
            display: flex; align-items: center; gap: 8px;
            padding: 10px 14px; cursor: pointer; user-select: none;
            font-weight: 600; font-size: 14px;
            border-radius: 8px; background: #f0f4f8;
            border: 1px solid #e0e6ec;
        }
        .folder-header i.fa-chevron-right, .folder-header i.fa-chevron-down {
            width: 14px; font-size: 11px; color: #888; transition: transform 0.2s;
        }
        .folder-header i.fa-folder { color: var(--bronze); }
        .folder-path { color: #666; font-weight: 400; font-size: 12px; margin-left: 4px; }
        .folder-count { margin-left: auto; font-size: 12px; color: #999; font-weight: 400; }
        .folder-checkbox { margin-right: 4px; transform: scale(1.15); cursor: pointer; accent-color: var(--sky-dark); }

        .folder-children { padding-left: 24px; }
        .file-row {
            display: flex; align-items: center; gap: 10px;
            padding: 8px 14px; border-radius: 6px;
            transition: background 0.15s;
            font-size: 13px;
        }
        .file-row:hover { background: #f5f8fb; }
        .file-row input[type="checkbox"] { transform: scale(1.1); cursor: pointer; flex-shrink: 0; accent-color: var(--sky-dark); }
        .file-icon { color: #aaa; flex-shrink: 0; width: 16px; text-align: center; }
        .file-old-name { color: var(--red); font-weight: 500; min-width: 0; word-break: break-all; }
        .file-arrow { color: #aaa; flex-shrink: 0; margin: 0 4px; }
        .file-new-name-input {
            color: var(--green); font-weight: 500; min-width: 120px; flex: 1;
            padding: 4px 8px; border: 2px solid transparent;
            border-radius: 6px; font-size: 13px; font-family: inherit;
            background: transparent; transition: all 0.2s;
        }
        .file-new-name-input:hover { border-color: #c8e6c9; background: #fafffa; }
        .file-new-name-input:focus {
            outline: none; border-color: var(--sky); background: #fff;
            box-shadow: 0 0 0 3px rgba(93,169,217,0.15);
        }
        .file-new-name-input.modified {
            border-color: var(--bronze-light); background: #fffdf5;
            box-shadow: 0 0 0 2px rgba(201,149,46,0.12);
        }
        .btn-reset-name {
            background: none; border: 1px solid #ddd; border-radius: 4px;
            cursor: pointer; color: #999; font-size: 11px; padding: 2px 6px;
            flex-shrink: 0; transition: all 0.15s; display: inline-flex;
            align-items: center; gap: 3px;
        }
        .btn-reset-name:hover { background: #f0f0f0; color: #666; border-color: #bbb; }
        .btn-reset-name.hidden { visibility: hidden; }
        .file-reason {
            font-size: 11px; color: #999; margin-left: auto; flex-shrink: 0;
            max-width: 200px; text-align: right; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }

        .custom-name-hint {
            background: #fff8e1; border: 1px solid #ffe082; border-radius: 8px;
            padding: 10px 16px; margin-top: 10px; margin-bottom: 4px;
            font-size: 12px; color: #6d4c00;
            display: flex; align-items: center; gap: 8px;
        }
        .custom-name-hint i { color: #f9a825; font-size: 14px; }

        /* NOTIFICATION / MODAL */
        .toast {
            position: fixed; top: 80px; right: 20px;
            padding: 14px 20px; border-radius: 10px;
            color: #fff; font-weight: 600; font-size: 14px;
            z-index: 9999; box-shadow: 0 6px 20px rgba(0,0,0,0.2);
            display: none; align-items: center; gap: 10px;
            max-width: 420px;
        }
        .toast.success { background: var(--green); display: flex; }
        .toast.error { background: var(--red); display: flex; }
        .toast.info { background: var(--sky-dark); display: flex; }

        .progress-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5); z-index: 9998;
            display: none; align-items: center; justify-content: center;
        }
        .progress-overlay.active { display: flex; }
        .progress-box {
            background: #fff; padding: 30px 40px; border-radius: 16px;
            text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        .progress-box .spinner {
            width: 40px; height: 40px; border: 4px solid #e0e0e0;
            border-top-color: var(--sky-dark); border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 14px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .progress-box p { font-weight: 600; color: var(--sky-dark); }

        .no-files {
            text-align: center; padding: 40px 20px; color: #999;
        }
        .no-files i { font-size: 48px; display: block; margin-bottom: 12px; color: #ccc; }

        .result-summary {
            background: var(--green-light); border: 1px solid #c8e6c9;
            border-radius: 12px; padding: 18px 20px; margin-top: 18px;
        }
        .result-summary h3 { color: var(--green); margin-bottom: 8px; font-size: 16px; }
        .result-summary p { font-size: 14px; color: #555; margin: 2px 0; }

        /* dev-info */
        .dev-info {
            background: linear-gradient(135deg, rgba(93,169,217,0.08), rgba(123,45,66,0.06));
            border-radius: 12px; padding: 18px 22px;
            border-left: 4px solid var(--bronze); margin-top: 16px;
        }
        .dev-info p { font-size: 13px; color: #666; margin: 3px 0; }
        .dev-info i { color: var(--bronze); margin-right: 6px; }

        .note-box {
            background: #fff8e1; border: 1px solid #ffe082; border-radius: 12px;
            padding: 14px 18px; margin-top: 14px;
            display: flex; align-items: flex-start; gap: 10px;
        }
        .note-box i { color: #f9a825; font-size: 18px; margin-top: 1px; }
        .note-box p { font-size: 13px; color: #6d4c00; line-height: 1.5; }

        @media (max-width: 650px) {
            .header { padding: 12px 14px; }
            .main-content { padding: 16px 8px; }
            .step-card { padding: 16px 14px; }
            .folder-select-row { flex-direction: column; }
            .folder-select-row .btn { width: 100%; justify-content: center; }
            .action-bar { gap: 6px; }
            .file-reason { display: none; }
        }
    </style>
</head>
<body>
    <!-- HEADER -->
    <div class="header">
        <div class="header-icon"><i class="fas fa-i-cursor"></i></div>
        <div>
            <div class="header-title">File Renamer - <span>Đổi tên hàng loạt file</span></div>
            <div class="header-sub"><i class="fas fa-folder-tree"></i> Chuẩn hóa tên file - Tự động hóa</div>
        </div>
    </div>

    <!-- MAIN -->
    <div class="main-content">
        <!-- STEP 1: Chọn thư mục -->
        <div class="step-card" id="step1">
            <h2><span class="step-num">1</span> <i class="fas fa-folder-open"></i> Chọn thư mục cần quét</h2>
            <p style="color:#777;font-size:13px;margin-bottom:12px;">
                Chọn thư mục cha chứa các file cần đổi tên. Tool sẽ tự động quét tất cả file
                trong thư mục con bên trong.
            </p>
            <div class="folder-select-row">
                <input type="text" class="folder-input" id="folderPath" placeholder="Dán đường dẫn thư mục vào đây..." />
                <button class="btn btn-browse" onclick="browseFolder()">
                    <i class="fas fa-search"></i> Chọn thư mục
                </button>
                <button class="btn btn-primary" onclick="scanFolder()">
                    <i class="fas fa-play"></i> Quét ngay
                </button>
            </div>
        </div>

        <!-- STEP 2: Kết quả & thực thi -->
        <div class="step-card" id="step2" style="display:none;">
            <h2><span class="step-num">2</span> <i class="fas fa-list-check"></i> Xem xét & đặt tên & xác nhận đổi tên</h2>

            <!-- Progress overlay -->
            <div class="progress-overlay" id="progressOverlay">
                <div class="progress-box">
                    <div class="spinner"></div>
                    <p id="progressText">Đang xử lý...</p>
                </div>
            </div>

            <!-- Toast -->
            <div class="toast" id="toast"></div>

            <!-- Hint về đặt tên tùy chỉnh -->
            <div class="custom-name-hint" id="customNameHint" style="display:none;">
                <i class="fas fa-pen-to-square"></i>
                <span><strong>Mẹo:</strong> Bạn có thể click vào tên mới <span style="color:var(--green);font-weight:600;">(màu xanh)</span> để tự đặt tên file theo ý muốn. Dùng nút <i class="fas fa-undo"></i> để khôi phục tên đề xuất.</span>
            </div>

            <!-- Stats -->
            <div class="stats-row" id="statsRow" style="display:none;">
                <span class="stat-badge warning" id="statTotal">0 file có vấn đề</span>
                <span class="stat-badge info" id="statSelected">0 file được chọn</span>
                <span class="stat-badge success" id="statCustom" style="display:none;">0 tên tùy chỉnh</span>
            </div>

            <!-- Action bar -->
            <div class="action-bar" id="actionBar" style="display:none;">
                <button class="btn btn-outline" onclick="selectAll()">
                    <i class="fas fa-check-square"></i> Chọn tất cả
                </button>
                <button class="btn btn-outline" onclick="deselectAll()">
                    <i class="fas fa-square"></i> Bỏ chọn tất cả
                </button>
                <span class="separator"></span>
                <button class="btn btn-outline" onclick="resetAllNames()">
                    <i class="fas fa-undo"></i> Khôi phục tên đề xuất
                </button>
                <span class="separator"></span>
                <button class="btn btn-success" id="btnExecute" onclick="executeRename()">
                    <i class="fas fa-rocket"></i> Thực thi đổi tên
                </button>
            </div>

            <!-- Tree -->
            <div class="tree-container" id="treeContainer"></div>

            <!-- Result summary (sau khi execute) -->
            <div id="resultSummary"></div>

            <!-- No files message -->
            <div class="no-files" id="noFiles" style="display:none;">
                <i class="fas fa-check-circle" style="color:#4caf50;"></i>
                <p>Tất cả tên file trong thư mục đều đạt chuẩn!</p>
                <p style="font-size:13px;">Không có file nào cần được đổi tên.</p>
            </div>
        </div>

        <!-- Thông tin -->
        <div class="step-card">
            <h2><i class="fas fa-info-circle"></i> Thông tin & cách sử dụng</h2>
            <ul style="list-style:none;padding:0;">
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 1:</strong> Chọn thư mục cha chứa các file cần đổi tên (tool tự quét cả thư mục con)</span>
                </li>
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 2:</strong> Xem danh sách file được đề xuất đổi tên - <strong style="color:var(--bronze);">Click vào tên mới để tự đặt tên</strong> theo ý muốn</span>
                </li>
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 3:</strong> Tích chọn các file muốn đổi tên (có thể chọn/bỏ chọn theo từng thư mục)</span>
                </li>
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 4:</strong> Bấm "Thực thi đổi tên" để tiến hành đổi tên các file đã chọn</span>
                </li>
            </ul>
            <div class="dev-info">
                <p><i class="fas fa-code"></i> Engine: <strong>FileRenamer</strong> - Chuẩn hóa Unicode, bỏ dấu, viết tắt, rút gọn tên</p>
                <p><i class="fas fa-pen-to-square"></i> Tùy chỉnh: <strong>Click vào tên mới để đặt tên theo ý muốn</strong> - Tên tùy chỉnh sẽ được ghi nhận và sử dụng khi đổi tên</p>
                <p><i class="fas fa-shield-alt"></i> An toàn: <strong>Luôn xem trước trước khi thực thi</strong> - Không tự động đổi tên</p>
            </div>
            <div class="note-box">
                <i class="fas fa-lightbulb"></i>
                <p><strong>Lưu ý:</strong> Tool chỉ đổi tên các file <strong>được tích chọn</strong>. Bạn có thể bỏ chọn bất kỳ file nào không muốn đổi tên. <strong style="color:var(--bronze);">Click vào ô tên mới (màu xanh) để tự đặt tên file</strong> - tên bạn nhập sẽ được ghi nhận và ưu tiên sử dụng thay vì tên đề xuất tự động.</p>
            </div>
        </div>
    </div>

    <script>
        // ============ STATE ============
        var scanData = null;      // {path, results: [{folder, old_name, new_name, reason, rel_path}]}
        var executeResults = null;

        // ============ FOLDER BROWSE ============
        function browseFolder() {
            fetch('/api/browse-folder')
                .then(r => r.json())
                .then(d => {
                    if (d.path) {
                        document.getElementById('folderPath').value = d.path;
                    }
                })
                .catch(e => {
                    alert('Không thể mở hộp thoại chọn thư mục. Hãy nhập đường dẫn thủ công.');
                });
        }

        // ============ SCAN ============
        function scanFolder() {
            var path = document.getElementById('folderPath').value.trim();
            if (!path) {
                showToast('Vui lòng nhập hoặc chọn đường dẫn thư mục.', 'error');
                return;
            }
            showProgress('Đang quét thư mục...');
            fetch('/api/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: path})
            })
            .then(r => r.json())
            .then(d => {
                hideProgress();
                if (d.error) {
                    showToast(d.error, 'error');
                    return;
                }
                scanData = d;
                renderResults(d);
            })
            .catch(e => {
                hideProgress();
                showToast('Lỗi kết nối đến server: ' + e, 'error');
            });
        }

        // ============ RENDER ============
        function renderResults(data) {
            var step2 = document.getElementById('step2');
            var treeContainer = document.getElementById('treeContainer');
            var noFiles = document.getElementById('noFiles');
            var statsRow = document.getElementById('statsRow');
            var actionBar = document.getElementById('actionBar');
            var resultSummary = document.getElementById('resultSummary');
            var customNameHint = document.getElementById('customNameHint');

            step2.style.display = 'block';
            resultSummary.innerHTML = '';
            executeResults = null;

            if (!data.results || data.results.length === 0) {
                treeContainer.innerHTML = '';
                noFiles.style.display = 'block';
                statsRow.style.display = 'none';
                actionBar.style.display = 'none';
                customNameHint.style.display = 'none';
                document.getElementById('statCustom').style.display = 'none';
                return;
            }

            noFiles.style.display = 'none';
            statsRow.style.display = 'flex';
            actionBar.style.display = 'flex';
            customNameHint.style.display = 'flex';

            // Group by folder
            var folders = {};
            for (var i = 0; i < data.results.length; i++) {
                var r = data.results[i];
                var folder = r.folder || '(Thư mục gốc)';
                if (!folders[folder]) folders[folder] = [];
                folders[folder].push(r);
            }

            // Sort folders
            var folderNames = Object.keys(folders).sort();

            var html = '';
            var fileIdx = 0;
            for (var fi = 0; fi < folderNames.length; fi++) {
                var fname = folderNames[fi];
                var files = folders[fname];
                // Sort files by old_name
                files.sort(function(a,b) { return (a.old_name||'').localeCompare(b.old_name||''); });

                html += '<div class="tree-folder">';
                html += '<div class="folder-header" onclick="toggleFolder(this)">';
                html += '<input type="checkbox" class="folder-checkbox" checked onclick="event.stopPropagation(); toggleFolderFiles(this)" data-folder="' + escHtml(fname) + '" />';
                html += '<i class="fas fa-chevron-down"></i>';
                html += '<i class="fas fa-folder"></i>';
                html += '<span>' + escHtml(fname) + '</span>';
                html += '<span class="folder-path">(' + files.length + ' file)</span>';
                html += '<span class="folder-count" style="margin-left:auto;">&nbsp;</span>';
                html += '</div>';
                html += '<div class="folder-children">';

                for (var fj = 0; fj < files.length; fj++) {
                    var f = files[fj];
                    var cbId = 'fcb_' + fileIdx;
                    var inpId = 'fni_' + fileIdx;
                    var rstId = 'frst_' + fileIdx;
                    html += '<div class="file-row">';
                    html += '<input type="checkbox" id="' + cbId + '" checked data-idx="' + fileIdx + '" data-folder="' + escHtml(fname) + '" onchange="updateStats()" />';
                    html += '<i class="fas fa-file-lines file-icon"></i>';
                    html += '<span class="file-old-name" title="' + escHtml(f.old_name) + '">' + escHtml(f.old_name) + '</span>';
                    html += '<i class="fas fa-arrow-right file-arrow"></i>';
                    html += '<input type="text" class="file-new-name-input" id="' + inpId + '" value="' + escHtmlAttr(f.new_name) + '" data-idx="' + fileIdx + '" data-original="' + escHtmlAttr(f.new_name) + '" oninput="onNameModified(this)" />';
                    html += '<button class="btn-reset-name hidden" id="' + rstId + '" title="Khôi phục tên đề xuất" onclick="resetSingleName(' + fileIdx + ')"><i class="fas fa-undo"></i></button>';
                    html += '<span class="file-reason" title="' + escHtml(f.reason) + '">' + escHtml(f.reason) + '</span>';
                    html += '</div>';
                    fileIdx++;
                }

                html += '</div></div>';
            }

            treeContainer.innerHTML = html;
            updateStats();
            document.getElementById('btnExecute').disabled = false;

            // Scroll to step2
            step2.scrollIntoView({behavior: 'smooth'});
        }

        function escHtml(str) {
            if (!str) return '';
            return str.replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>').replace(/"/g,'"');
        }

        function escHtmlAttr(str) {
            if (!str) return '';
            return str.replace(/&/g,'&').replace(/"/g,'"').replace(/</g,'<').replace(/>/g,'>');
        }

        function toggleFolder(header) {
            var children = header.nextElementSibling;
            var icon = header.querySelector('.fa-chevron-down, .fa-chevron-right');
            if (children.style.display === 'none') {
                children.style.display = 'block';
                icon.className = 'fas fa-chevron-down';
            } else {
                children.style.display = 'none';
                icon.className = 'fas fa-chevron-right';
            }
        }

        function toggleFolderFiles(checkbox) {
            var folder = checkbox.getAttribute('data-folder');
            var checked = checkbox.checked;
            var allCbs = document.querySelectorAll('.file-row input[type="checkbox"]');
            for (var i = 0; i < allCbs.length; i++) {
                if (allCbs[i].getAttribute('data-folder') === folder) {
                    allCbs[i].checked = checked;
                }
            }
            updateStats();
        }

        // ============ CUSTOM NAME HANDLING ============
        function onNameModified(input) {
            var idx = input.getAttribute('data-idx');
            var original = input.getAttribute('data-original');
            var currentVal = input.value.trim();
            var rstBtn = document.getElementById('frst_' + idx);

            if (currentVal !== original && currentVal !== '') {
                input.classList.add('modified');
                if (rstBtn) rstBtn.classList.remove('hidden');
            } else if (currentVal === original) {
                input.classList.remove('modified');
                if (rstBtn) rstBtn.classList.add('hidden');
            } else {
                // empty - keep modified style but allow reset
                input.classList.add('modified');
                if (rstBtn) rstBtn.classList.remove('hidden');
            }
            updateStats();
        }

        function resetSingleName(idx) {
            var inp = document.getElementById('fni_' + idx);
            var rstBtn = document.getElementById('frst_' + idx);
            if (inp) {
                inp.value = inp.getAttribute('data-original');
                inp.classList.remove('modified');
                if (rstBtn) rstBtn.classList.add('hidden');
                updateStats();
            }
        }

        function resetAllNames() {
            var allInputs = document.querySelectorAll('.file-new-name-input');
            for (var i = 0; i < allInputs.length; i++) {
                var inp = allInputs[i];
                inp.value = inp.getAttribute('data-original');
                inp.classList.remove('modified');
                var idx = inp.getAttribute('data-idx');
                var rstBtn = document.getElementById('frst_' + idx);
                if (rstBtn) rstBtn.classList.add('hidden');
            }
            updateStats();
            showToast('Đã khôi phục tất cả về tên đề xuất.', 'info');
        }

        function getCustomNames() {
            var custom = {};
            var allInputs = document.querySelectorAll('.file-new-name-input');
            for (var i = 0; i < allInputs.length; i++) {
                var inp = allInputs[i];
                var idx = parseInt(inp.getAttribute('data-idx'));
                var original = inp.getAttribute('data-original');
                var currentVal = inp.value.trim();
                if (currentVal && currentVal !== original) {
                    custom[idx] = currentVal;
                }
            }
            return custom;
        }

        function updateStats() {
            var allCbs = document.querySelectorAll('.file-row input[type="checkbox"]');
            var total = allCbs.length;
            var selected = 0;
            for (var i = 0; i < allCbs.length; i++) {
                if (allCbs[i].checked) selected++;
            }
            document.getElementById('statTotal').innerHTML = '<i class="fas fa-exclamation-triangle"></i> ' + total + ' file có vấn đề';
            document.getElementById('statSelected').innerHTML = '<i class="fas fa-check"></i> ' + selected + ' file được chọn';

            // Count custom names
            var customNames = getCustomNames();
            var customCount = Object.keys(customNames).length;
            var statCustom = document.getElementById('statCustom');
            if (customCount > 0) {
                statCustom.style.display = 'inline-flex';
                statCustom.innerHTML = '<i class="fas fa-pen-to-square"></i> ' + customCount + ' tên tùy chỉnh';
            } else {
                statCustom.style.display = 'none';
            }
        }

        function selectAll() {
            var allCbs = document.querySelectorAll('.file-row input[type="checkbox"]');
            var folderCbs = document.querySelectorAll('.folder-checkbox');
            for (var i = 0; i < allCbs.length; i++) allCbs[i].checked = true;
            for (var i = 0; i < folderCbs.length; i++) folderCbs[i].checked = true;
            updateStats();
        }

        function deselectAll() {
            var allCbs = document.querySelectorAll('.file-row input[type="checkbox"]');
            var folderCbs = document.querySelectorAll('.folder-checkbox');
            for (var i = 0; i < allCbs.length; i++) allCbs[i].checked = false;
            for (var i = 0; i < folderCbs.length; i++) folderCbs[i].checked = false;
            updateStats();
        }

        // ============ EXECUTE ============
        function executeRename() {
            if (!scanData || !scanData.results) return;

            var allCbs = document.querySelectorAll('.file-row input[type="checkbox"]');
            var selectedIndices = [];
            for (var i = 0; i < allCbs.length; i++) {
                if (allCbs[i].checked) {
                    selectedIndices.push(parseInt(allCbs[i].getAttribute('data-idx')));
                }
            }

            if (selectedIndices.length === 0) {
                showToast('Vui lòng chọn ít nhất 1 file để đổi tên.', 'error');
                return;
            }

            // Collect custom names
            var customNames = getCustomNames();
            var customCount = Object.keys(customNames).length;

            var confirmMsg = 'Bạn có CHẮC CHẮN muốn đổi tên ' + selectedIndices.length + ' file đã chọn?';
            if (customCount > 0) {
                confirmMsg += '\n\nTrong đó có ' + customCount + ' file được đặt tên tùy chỉnh.';
            }
            confirmMsg += '\n\nHành động này KHÔNG THỂ HOÀN TÁC.\n\nBấm OK để tiếp tục.';

            if (!confirm(confirmMsg)) {
                return;
            }

            showProgress('Đang đổi tên ' + selectedIndices.length + ' file...');
            document.getElementById('btnExecute').disabled = true;

            fetch('/api/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    path: scanData.path,
                    indices: selectedIndices,
                    custom_names: customNames
                })
            })
            .then(r => r.json())
            .then(d => {
                hideProgress();
                document.getElementById('btnExecute').disabled = false;
                executeResults = d;
                showExecuteResult(d);
            })
            .catch(e => {
                hideProgress();
                document.getElementById('btnExecute').disabled = false;
                showToast('Lỗi: ' + e, 'error');
            });
        }

        function showExecuteResult(d) {
            var resultSummary = document.getElementById('resultSummary');
            var html = '<div class="result-summary">';
            html += '<h3><i class="fas fa-clipboard-check"></i> Kết quả thực thi</h3>';
            html += '<p><strong>Tổng số file được chọn:</strong> ' + (d.total || 0) + '</p>';
            html += '<p style="color:var(--green);"><strong>Đã đổi tên thành công:</strong> ' + (d.renamed || 0) + '</p>';
            if (d.custom_used > 0) {
                html += '<p style="color:var(--bronze);"><strong>Tên tùy chỉnh đã dùng:</strong> ' + d.custom_used + '</p>';
            }
            if (d.errors > 0) {
                html += '<p style="color:var(--red);"><strong>Lỗi:</strong> ' + d.errors + '</p>';
            }
            if (d.skipped > 0) {
                html += '<p style="color:#f57f17;"><strong>Bỏ qua:</strong> ' + d.skipped + '</p>';
            }
            if (d.details && d.details.length > 0) {
                html += '<div style="margin-top:10px;max-height:200px;overflow-y:auto;">';
                for (var i = 0; i < d.details.length; i++) {
                    var det = d.details[i];
                    var icon = det.status === 'renamed' ? '<i class="fas fa-check-circle" style="color:var(--green);"></i>' :
                               (det.status === 'error' ? '<i class="fas fa-times-circle" style="color:var(--red);"></i>' :
                               '<i class="fas fa-minus-circle" style="color:#f57f17;"></i>');
                    html += '<p style="font-size:12px;margin:3px 0;">' + icon + ' ' + escHtml(det.file || '') + ' -> ' + escHtml(det.new_name || '') + '</p>';
                    if (det.error) {
                        html += '<p style="font-size:11px;color:var(--red);margin-left:22px;">Lỗi: ' + escHtml(det.error) + '</p>';
                    }
                }
                html += '</div>';
            }
            html += '</div>';
            resultSummary.innerHTML = html;
            resultSummary.scrollIntoView({behavior: 'smooth'});

            if (d.renamed > 0) {
                showToast('Đã đổi tên thành công ' + d.renamed + ' file!', 'success');
            }
        }

        // ============ UI HELPERS ============
        function showToast(msg, type) {
            var t = document.getElementById('toast');
            t.className = 'toast ' + (type || 'info');
            t.innerHTML = msg;
            t.style.display = 'flex';
            clearTimeout(t._timeout);
            t._timeout = setTimeout(function() { t.style.display = 'none'; }, 4000);
        }

        function showProgress(msg) {
            document.getElementById('progressText').textContent = msg || 'Đang xử lý...';
            document.getElementById('progressOverlay').classList.add('active');
        }

        function hideProgress() {
            document.getElementById('progressOverlay').classList.remove('active');
        }

        // Enter key to scan
        document.getElementById('folderPath').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') scanFolder();
        });
    </script>
</body>
</html>'''


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route('/')
def index():
    return HTML_TEMPLATE


@app.route('/api/browse-folder')
def browse_folder():
    """Mở hộp thoại chọn thư mục native Windows."""
    try:
        folder = browse_folder_windows('Chọn thư mục cần quét')
        if folder:
            folder = os.path.normpath(folder)
        return jsonify({'path': folder or ''})
    except Exception as e:
        return jsonify({'path': '', 'error': str(e)})


@app.route('/api/scan', methods=['POST'])
def scan_folder():
    """Quét thư mục và trả về danh sách file có vấn đề."""
    data = request.get_json()
    folder_path = data.get('path', '').strip()

    if not folder_path:
        return jsonify({'error': 'Vui lòng nhập đường dẫn thư mục.'})
    if not os.path.isdir(folder_path):
        return jsonify({'error': f'Thư mục không tồn tại: {folder_path}'})

    try:
        ws = Path(folder_path).resolve()
        # Sử dụng file_renamer để quét
        problematic = renamer.scan_workspace(str(ws), recursive=True)

        results = []
        for rel_path in problematic:
            full_path = ws / rel_path
            old_name = full_path.name
            is_problem, reasons = renamer.is_problematic_name(old_name)
            if not is_problem:
                continue
            new_name = renamer.generate_clean_name(old_name)
            if new_name == old_name:
                continue
            # Xác định folder
            folder_rel = str(Path(rel_path).parent) if Path(rel_path).parent != Path('.') else '(Thư mục gốc)'
            reason_text = '; '.join(reasons)
            results.append({
                'folder': folder_rel,
                'old_name': old_name,
                'new_name': new_name,
                'reason': reason_text,
                'rel_path': rel_path
            })

        return jsonify({
            'path': str(ws),
            'results': results,
            'total_scanned': len(problematic),
            'total_problematic': len(results)
        })
    except Exception as e:
        return jsonify({'error': f'Lỗi khi quét thư mục: {str(e)}'})


@app.route('/api/execute', methods=['POST'])
def execute_rename():
    """Thực thi đổi tên các file đã chọn, hỗ trợ tên tùy chỉnh."""
    data = request.get_json()
    folder_path = data.get('path', '')
    indices = data.get('indices', [])
    custom_names = data.get('custom_names', {})
    # Convert custom_names keys from string to int (JSON keys are always strings)
    custom_names = {int(k): v for k, v in custom_names.items()}

    if not folder_path or not os.path.isdir(folder_path):
        return jsonify({'error': 'Đường dẫn thư mục không hợp lệ.'})
    if not indices:
        return jsonify({'error': 'Không có file nào được chọn.'})

    ws = Path(folder_path).resolve()

    # Quét lại để có danh sách file
    problematic = renamer.scan_workspace(str(ws), recursive=True)

    # Build list of (rel_path, new_name) từ file_renamer cho các file đã chọn
    all_results = []
    for rel_path in problematic:
        full_path = ws / rel_path
        old_name = full_path.name
        is_problem, reasons = renamer.is_problematic_name(old_name)
        if not is_problem:
            continue
        new_name = renamer.generate_clean_name(old_name)
        if new_name == old_name:
            continue
        all_results.append({
            'rel_path': rel_path,
            'new_name': new_name,
            'reasons': '; '.join(reasons)
        })

    # Chọn các file theo indices
    selected = [all_results[i] for i in indices if i < len(all_results)]

    total = len(selected)
    renamed = 0
    errors = 0
    skipped = 0
    custom_used = 0
    details = []

    for idx_in_list, item in enumerate(selected):
        rel_path = item['rel_path']
        full_path = ws / rel_path
        old_name = full_path.name

        # Determine the actual new name: custom if provided, else auto-generated
        original_index = indices[idx_in_list]  # the original index in all_results
        if original_index in custom_names:
            custom_name = custom_names[original_index].strip()
            if custom_name:
                new_name = custom_name
                custom_used += 1
            else:
                new_name = item['new_name']
        else:
            new_name = item['new_name']

        if not full_path.exists():
            errors += 1
            details.append({'file': rel_path, 'new_name': new_name, 'status': 'error', 'error': 'File không tồn tại'})
            continue

        new_full_path = full_path.parent / new_name

        # Kiểm tra trùng tên
        if new_full_path.exists() and new_full_path != full_path:
            stem = Path(new_name).stem
            suffix = Path(new_name).suffix
            counter = 1
            while new_full_path.exists():
                new_name = f"{stem}_{counter}{suffix}"
                new_full_path = full_path.parent / new_name
                counter += 1
                if counter > 100:
                    break
            if counter > 100:
                errors += 1
                details.append({'file': rel_path, 'new_name': new_name, 'status': 'error', 'error': 'Không thể tạo tên không trùng sau 100 lần thử'})
                continue

        try:
            full_path.rename(new_full_path)
            renamed += 1
            details.append({'file': rel_path, 'new_name': new_name, 'status': 'renamed', 'error': None})
        except Exception as e:
            errors += 1
            details.append({'file': rel_path, 'new_name': new_name, 'status': 'error', 'error': str(e)})

    return jsonify({
        'total': total,
        'renamed': renamed,
        'errors': errors,
        'skipped': skipped,
        'custom_used': custom_used,
        'details': details
    })


# ============================================================
# MAIN
# ============================================================

def main():
    host = '127.0.0.1'
    port = 5789

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print('=' * 60)
    print('  FILE RENAMER - GUI')
    print('=' * 60)
    print(f'  Server dang chay tai: http://{host}:{port}')
    print('  Nhan Ctrl+C de thoat.')
    print('=' * 60)

    # Mở trình duyệt sau 1.5 giây
    def open_browser():
        webbrowser.open(f'http://{host}:{port}')

    threading.Timer(1.5, open_browser).start()

    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    main()