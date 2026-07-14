# -*- coding: utf-8 -*-
"""
DocxToMd GUI - Công cụ chuyển đổi Word (.doc/.docx) sang Markdown (Web-based GUI)
=================================================================================
Flask backend + HTML/JS frontend tích hợp trong 1 file Python.
Sử dụng: python docx_to_md_gui.py

Chức năng:
  - Quét đệ quy thư mục cha, tìm file .doc/.docx
  - Hiển thị cây thư mục với danh sách file
  - Chọn/bỏ chọn file để chuyển đổi
  - .docx: dùng python-docx (thuần Python)
  - .doc:  dùng win32com (Word COM Automation) → lưu tạm .docx → python-docx
  - Giữ nguyên file gốc, tạo file .md bên cạnh
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
    "docx": "python-docx",
    "pythoncom": "pywin32",
})

import json
import time
import threading
import webbrowser
import ctypes
from ctypes import wintypes
from pathlib import Path

from flask import Flask, request, jsonify

# ============================================================
# IMPORT ENGINE TỪ convert_doc_to_md (cùng thư mục)
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from convert_doc_to_md import (
        read_docx_text,
        read_doc_via_win32com,
        scan_directory,
    )
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False
    print("[WARNING] Không thể import convert_doc_to_md. Dùng engine dự phòng.")

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

    CoInitialize(None)

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

app = Flask(__name__, static_folder=None)

# ============================================================
# ENGINE DỰ PHÒNG (nếu không import được từ Docx_to_md)
# ============================================================
if not ENGINE_AVAILABLE:
    def read_docx_text(file_path):
        try:
            from docx import Document
        except ImportError:
            return None
        try:
            # Dùng str(Path) để chuẩn hóa đường dẫn Unicode
            doc = Document(str(Path(file_path)))
        except Exception:
            return None
        text_lines = []
        for para in doc.paragraphs:
            t = para.text.strip()
            if t:
                text_lines.append(t)
        for table_idx, table in enumerate(doc.tables, 1):
            text_lines.append(f"\n### Bảng {table_idx}")
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                text_lines.append(" | ".join(row_data))
        if not text_lines:
            return None
        return "\n\n".join(text_lines)

    def read_doc_via_win32com(file_path):
        import pythoncom
        import win32com.client
        import tempfile
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return None, "File không tồn tại"
        # Lấy short path để tránh lỗi Unicode với Word COM Automation
        try:
            _buf = ctypes.create_unicode_buffer(300)
            ctypes.windll.kernel32.GetShortPathNameW(str(Path(abs_path)), _buf, 300)
            short_path = _buf.value or abs_path
        except Exception:
            short_path = abs_path
        word = None
        doc = None
        temp_docx = None
        try:
            pythoncom.CoInitialize()
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False
            doc = word.Documents.Open(short_path, ReadOnly=True)
            temp_fd, temp_docx = tempfile.mkstemp(suffix=".docx", prefix="temp_doc_")
            os.close(temp_fd)
            doc.SaveAs2(temp_docx, FileFormat=16)
            doc.Close(SaveChanges=False)
            doc = None
            text = read_docx_text(temp_docx)
            return text, None
        except Exception as e:
            return None, str(e)
        finally:
            try:
                if doc is not None:
                    doc.Close(SaveChanges=False)
            except:
                pass
            try:
                if word is not None:
                    word.Quit()
            except:
                pass
            try:
                pythoncom.CoUninitialize()
            except:
                pass
            if temp_docx and os.path.exists(temp_docx):
                try:
                    os.remove(temp_docx)
                except:
                    pass

    def scan_directory(root_dir, force=False, skip_doc=False):
        if not os.path.isdir(root_dir):
            return []
        extensions = [".docx"]
        if not skip_doc:
            extensions.append(".doc")
        files_to_convert = []
        for dirpath, dirnames, filenames in os.walk(root_dir):
            for filename in filenames:
                ext = Path(filename).suffix.lower()
                if ext not in extensions:
                    continue
                source_path = os.path.join(dirpath, filename)
                stem = Path(filename).stem
                md_path = os.path.join(dirpath, stem + ".md")
                if not force and os.path.exists(md_path):
                    continue
                files_to_convert.append((ext, source_path, md_path))
        return files_to_convert


# ============================================================
# HTML TEMPLATE
# ============================================================
HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocxToMd - Chuyển đổi Word sang Markdown</title>
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
            --orange: #e65100; --orange-light: #fff3e0;
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

        .options-row {
            display: flex; gap: 20px; align-items: center; flex-wrap: wrap;
            margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border);
        }
        .option-label {
            display: flex; align-items: center; gap: 8px; font-size: 13px;
            color: #555; cursor: pointer; user-select: none;
        }
        .option-label input[type="checkbox"] {
            transform: scale(1.15); cursor: pointer;
            accent-color: var(--sky-dark);
        }

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
        .stat-badge.orange { background: var(--orange-light); color: var(--orange); }

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
        .file-icon { flex-shrink: 0; width: 18px; text-align: center; }
        .file-icon.docx { color: var(--sky); }
        .file-icon.doc { color: var(--orange); }
        .file-icon.has-md { color: var(--green); }
        .file-name { font-weight: 500; min-width: 0; word-break: break-all; flex: 1; }
        .file-name.has-md-name { color: #999; text-decoration: line-through; }
        .file-ext {
            font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px;
            flex-shrink: 0; margin-left: 8px;
        }
        .file-ext.docx { background: #e3f2fd; color: var(--sky-dark); }
        .file-ext.doc { background: var(--orange-light); color: var(--orange); }
        .file-md-status {
            font-size: 11px; flex-shrink: 0; margin-left: 8px;
            padding: 2px 8px; border-radius: 4px;
        }
        .file-md-status.exists { background: var(--green-light); color: var(--green); }
        .file-md-status.new { background: #f5f5f5; color: #999; }

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

        .toast {
            position: fixed; top: 80px; right: 20px;
            padding: 14px 20px; border-radius: 10px;
            color: #fff; font-weight: 600; font-size: 14px;
            z-index: 9999; box-shadow: 0 6px 20px rgba(0,0,0,0.2);
            display: none; align-items: center; gap: 10px;
            max-width: 420px;
        }
        .toast.success { background: var(--green); }
        .toast.error { background: var(--red); }
        .toast.info { background: var(--sky-dark); }

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
            .options-row { flex-direction: column; gap: 10px; }
        }
    </style>
</head>
<body>
    <!-- HEADER -->
    <div class="header">
        <div class="header-icon"><i class="fas fa-file-word"></i></div>
        <div>
            <div class="header-title">DocxToMd - <span>Chuyển đổi Word sang Markdown</span></div>
            <div class="header-sub"><i class="fas fa-folder-tree"></i> .doc / .docx → .md — Hàng loạt, tự động</div>
        </div>
    </div>

    <!-- MAIN -->
    <div class="main-content">
        <!-- STEP 1: Chọn thư mục -->
        <div class="step-card" id="step1">
            <h2><span class="step-num">1</span> <i class="fas fa-folder-open"></i> Chọn thư mục cần quét</h2>
            <p style="color:#777;font-size:13px;margin-bottom:12px;">
                Chọn thư mục cha chứa các file Word (.doc/.docx). Tool sẽ tự động quét tất cả 
                thư mục con bên trong và tạo file .md tương ứng bên cạnh file gốc.
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
            <div class="options-row">
                <label class="option-label" title="Bỏ qua file .doc (chỉ xử lý .docx). Hữu ích khi không có Microsoft Word.">
                    <input type="checkbox" id="optSkipDoc" />
                    <i class="fas fa-file-word" style="color:var(--orange);"></i> Bỏ qua file .doc (chỉ xử lý .docx)
                </label>
                <label class="option-label" title="Ghi đè file .md nếu đã tồn tại (mặc định bỏ qua file đã có .md)">
                    <input type="checkbox" id="optForce" />
                    <i class="fas fa-rotate-right" style="color:var(--sky-dark);"></i> Ghi đè file .md cũ
                </label>
            </div>
        </div>

        <!-- STEP 2: Kết quả & thực thi -->
        <div class="step-card" id="step2" style="display:none;">
            <h2><span class="step-num">2</span> <i class="fas fa-list-check"></i> Xem xét & xác nhận chuyển đổi</h2>

            <!-- Progress overlay -->
            <div class="progress-overlay" id="progressOverlay">
                <div class="progress-box">
                    <div class="spinner"></div>
                    <p id="progressText">Đang xử lý...</p>
                    <p id="progressSub" style="font-size:12px;color:#999;margin-top:4px;"></p>
                </div>
            </div>

            <!-- Toast -->
            <div class="toast" id="toast"></div>

            <!-- Stats -->
            <div class="stats-row" id="statsRow" style="display:none;">
                <span class="stat-badge info" id="statTotal">0 file tìm thấy</span>
                <span class="stat-badge success" id="statDocx">0 .docx</span>
                <span class="stat-badge orange" id="statDoc">0 .doc</span>
                <span class="stat-badge warning" id="statSelected">0 file được chọn</span>
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
                <button class="btn btn-success" id="btnExecute" onclick="executeConvert()">
                    <i class="fas fa-rocket"></i> Thực thi chuyển đổi
                </button>
            </div>

            <!-- Tree -->
            <div class="tree-container" id="treeContainer"></div>

            <!-- Result summary -->
            <div id="resultSummary"></div>

            <!-- No files message -->
            <div class="no-files" id="noFiles" style="display:none;">
                <i class="fas fa-check-circle" style="color:#4caf50;"></i>
                <p>Không tìm thấy file Word nào cần chuyển đổi!</p>
                <p style="font-size:13px;">Tất cả file đã có .md hoặc không có file .doc/.docx trong thư mục.</p>
            </div>
        </div>

        <!-- Thông tin -->
        <div class="step-card">
            <h2><i class="fas fa-info-circle"></i> Thông tin & cách sử dụng</h2>
            <ul style="list-style:none;padding:0;">
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 1:</strong> Chọn thư mục cha chứa file Word (tool tự quét cả thư mục con)</span>
                </li>
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 2:</strong> Xem danh sách file .doc/.docx hiển thị theo cây thư mục</span>
                </li>
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 3:</strong> Tích chọn file muốn chuyển đổi (có thể chọn theo từng thư mục)</span>
                </li>
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 4:</strong> Bấm "Thực thi chuyển đổi" để tạo file .md bên cạnh file gốc</span>
                </li>
            </ul>
            <div class="dev-info">
                <p><i class="fas fa-cog"></i> Engine: <strong>python-docx + win32com</strong> — Trích xuất text từ Word sang Markdown</p>
                <p><i class="fas fa-shield-alt"></i> An toàn: <strong>File gốc được giữ nguyên</strong> — Chỉ tạo thêm file .md bên cạnh</p>
                <p><i class="fas fa-info-circle"></i> File .doc: cần <strong>Microsoft Word</strong> để chuyển đổi. File .docx: không cần Word.</p>
            </div>
            <div class="note-box">
                <i class="fas fa-lightbulb"></i>
                <p><strong>Lưu ý:</strong> Công cụ <strong>giữ nguyên file gốc</strong> (.doc/.docx), chỉ tạo thêm file .md bên cạnh. Nếu máy bạn không có Microsoft Word, hãy tích chọn <strong>"Bỏ qua file .doc"</strong> để chỉ xử lý file .docx.</p>
            </div>
        </div>
    </div>

    <script>
        // ============ STATE ============
        var scanData = null;      // {path, files: [{ext, source_path, md_path, folder, md_exists}]}
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
            var skipDoc = document.getElementById('optSkipDoc').checked;
            var force = document.getElementById('optForce').checked;

            showProgress('Đang quét thư mục...');
            fetch('/api/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: path, skip_doc: skipDoc, force: force})
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

            step2.style.display = 'block';
            resultSummary.innerHTML = '';
            executeResults = null;

            if (!data.files || data.files.length === 0) {
                treeContainer.innerHTML = '';
                noFiles.style.display = 'block';
                statsRow.style.display = 'none';
                actionBar.style.display = 'none';
                return;
            }

            noFiles.style.display = 'none';
            statsRow.style.display = 'flex';
            actionBar.style.display = 'flex';

            // Stats
            var totalDocx = 0, totalDoc = 0;
            for (var i = 0; i < data.files.length; i++) {
                if (data.files[i].ext === '.docx') totalDocx++;
                else if (data.files[i].ext === '.doc') totalDoc++;
            }
            document.getElementById('statTotal').innerHTML = '<i class="fas fa-file"></i> ' + data.files.length + ' file tìm thấy';
            document.getElementById('statDocx').innerHTML = '<i class="fas fa-file-word"></i> ' + totalDocx + ' .docx';
            document.getElementById('statDoc').innerHTML = '<i class="fas fa-file"></i> ' + totalDoc + ' .doc';

            // Group by folder
            var folders = {};
            for (var i = 0; i < data.files.length; i++) {
                var f = data.files[i];
                var folder = f.folder || '(Thư mục gốc)';
                if (!folders[folder]) folders[folder] = [];
                folders[folder].push(f);
            }

            var folderNames = Object.keys(folders).sort();

            var html = '';
            var fileIdx = 0;
            for (var fi = 0; fi < folderNames.length; fi++) {
                var fname = folderNames[fi];
                var files = folders[fname];
                files.sort(function(a,b) { return (a.filename||'').localeCompare(b.filename||''); });

                html += '<div class="tree-folder">';
                html += '<div class="folder-header" onclick="toggleFolder(this)">';
                html += '<input type="checkbox" class="folder-checkbox" checked onclick="event.stopPropagation(); toggleFolderFiles(this)" data-folder="' + escHtml(fname) + '" />';
                html += '<i class="fas fa-chevron-down"></i>';
                html += '<i class="fas fa-folder"></i>';
                html += '<span>' + escHtml(fname) + '</span>';
                html += '<span class="folder-count">' + files.length + ' file</span>';
                html += '</div>';
                html += '<div class="folder-children">';

                for (var fj = 0; fj < files.length; fj++) {
                    var f = files[fj];
                    var cbId = 'fcb_' + fileIdx;
                    var isDocx = f.ext === '.docx';
                    var hasMd = f.md_exists;

                    html += '<div class="file-row">';
                    html += '<input type="checkbox" id="' + cbId + '" ' + (hasMd ? '' : 'checked') + ' data-idx="' + fileIdx + '" data-folder="' + escHtml(fname) + '" onchange="updateStats()" />';

                    // Icon
                    if (hasMd) {
                        html += '<i class="fas fa-check-circle file-icon has-md" title="Đã có file .md"></i>';
                    } else if (isDocx) {
                        html += '<i class="fas fa-file-word file-icon docx" title="File .docx"></i>';
                    } else {
                        html += '<i class="fas fa-file file-icon doc" title="File .doc (cần MS Word)"></i>';
                    }

                    // Name
                    html += '<span class="file-name' + (hasMd ? ' has-md-name' : '') + '" title="' + escHtml(f.filename) + '">' + escHtml(f.filename) + '</span>';

                    // Extension badge
                    html += '<span class="file-ext ' + f.ext.replace('.','') + '">' + f.ext + '</span>';

                    // MD status
                    if (hasMd) {
                        html += '<span class="file-md-status exists">Đã có .md</span>';
                    } else {
                        html += '<span class="file-md-status new">→ Sẽ tạo .md</span>';
                    }

                    html += '</div>';
                    fileIdx++;
                }

                html += '</div></div>';
            }

            treeContainer.innerHTML = html;
            updateStats();
            document.getElementById('btnExecute').disabled = false;

            step2.scrollIntoView({behavior: 'smooth'});
        }

        function escHtml(str) {
            if (!str) return '';
            return str.replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>').replace(/"/g,'"');
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

        function updateStats() {
            var allCbs = document.querySelectorAll('.file-row input[type="checkbox"]');
            var total = allCbs.length;
            var selected = 0;
            for (var i = 0; i < allCbs.length; i++) {
                if (allCbs[i].checked) selected++;
            }
            document.getElementById('statSelected').innerHTML = '<i class="fas fa-check"></i> ' + selected + ' file được chọn';
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
        function executeConvert() {
            if (!scanData || !scanData.files) return;

            var allCbs = document.querySelectorAll('.file-row input[type="checkbox"]');
            var selectedIndices = [];
            for (var i = 0; i < allCbs.length; i++) {
                if (allCbs[i].checked) {
                    selectedIndices.push(parseInt(allCbs[i].getAttribute('data-idx')));
                }
            }

            if (selectedIndices.length === 0) {
                showToast('Vui lòng chọn ít nhất 1 file để chuyển đổi.', 'error');
                return;
            }

            var hasDocFiles = false;
            for (var i = 0; i < selectedIndices.length; i++) {
                if (scanData.files[selectedIndices[i]].ext === '.doc') {
                    hasDocFiles = true;
                    break;
                }
            }

            var confirmMsg = 'Bạn có CHẮC CHẮN muốn chuyển đổi ' + selectedIndices.length + ' file đã chọn?\n\n' +
                'File .md sẽ được tạo cùng thư mục với file gốc.\n' +
                'File gốc (.doc/.docx) sẽ được GIỮ NGUYÊN.\n';
            if (hasDocFiles) {
                confirmMsg += '\n⚠ File .doc cần Microsoft Word để chuyển đổi.\n';
            }
            confirmMsg += '\nBấm OK để tiếp tục.';

            if (!confirm(confirmMsg)) {
                return;
            }

            showProgress('Đang chuyển đổi ' + selectedIndices.length + ' file...', '');
            document.getElementById('btnExecute').disabled = true;

            fetch('/api/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    path: scanData.path,
                    indices: selectedIndices
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
            html += '<h3><i class="fas fa-clipboard-check"></i> Kết quả chuyển đổi</h3>';
            html += '<p><strong>Tổng số file được chọn:</strong> ' + (d.total || 0) + '</p>';
            html += '<p style="color:var(--green);"><strong>Đã chuyển đổi thành công:</strong> ' + (d.ok || 0) + '</p>';
            if (d.notext > 0) {
                html += '<p style="color:#f57f17;"><strong>Không có nội dung text:</strong> ' + d.notext + '</p>';
            }
            if (d.errors > 0) {
                html += '<p style="color:var(--red);"><strong>Lỗi:</strong> ' + d.errors + '</p>';
            }
            if (d.details && d.details.length > 0) {
                html += '<div style="margin-top:10px;max-height:240px;overflow-y:auto;">';
                for (var i = 0; i < d.details.length; i++) {
                    var det = d.details[i];
                    var icon = det.status === 'ok' ? '<i class="fas fa-check-circle" style="color:var(--green);"></i>' :
                               (det.status === 'notext' ? '<i class="fas fa-minus-circle" style="color:#f57f17;"></i>' :
                               '<i class="fas fa-times-circle" style="color:var(--red);"></i>');
                    html += '<p style="font-size:12px;margin:3px 0;">' + icon + ' ' + escHtml(det.file || '') + ' → ' + escHtml(det.md_name || '') + '</p>';
                    if (det.error) {
                        html += '<p style="font-size:11px;color:var(--red);margin-left:22px;">Lỗi: ' + escHtml(det.error) + '</p>';
                    }
                }
                html += '</div>';
            }
            html += '</div>';
            resultSummary.innerHTML = html;
            resultSummary.scrollIntoView({behavior: 'smooth'});

            if (d.ok > 0) {
                showToast('Đã chuyển đổi thành công ' + d.ok + ' file!', 'success');
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

        function showProgress(msg, sub) {
            document.getElementById('progressText').textContent = msg || 'Đang xử lý...';
            document.getElementById('progressSub').textContent = sub || '';
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
        folder = browse_folder_windows('Chọn thư mục cha chứa file Word')
        if folder:
            folder = os.path.normpath(folder)
        return jsonify({'path': folder or ''})
    except Exception as e:
        return jsonify({'path': '', 'error': str(e)})


@app.route('/api/scan', methods=['POST'])
def scan_folder():
    """Quét thư mục và trả về danh sách file .doc/.docx."""
    data = request.get_json()
    folder_path = data.get('path', '').strip()
    skip_doc = data.get('skip_doc', False)
    force = data.get('force', False)

    if not folder_path:
        return jsonify({'error': 'Vui lòng nhập đường dẫn thư mục.'})
    if not os.path.isdir(folder_path):
        return jsonify({'error': f'Thư mục không tồn tại: {folder_path}'})

    try:
        files = scan_directory(folder_path, force=force, skip_doc=skip_doc)

        results = []
        for ext, source_path, md_path in files:
            filename = os.path.basename(source_path)
            # Tính folder tương đối
            rel_dir = os.path.relpath(os.path.dirname(source_path), folder_path)
            if rel_dir == '.':
                folder_display = '(Thư mục gốc)'
            else:
                folder_display = rel_dir

            md_exists = os.path.exists(md_path)

            results.append({
                'ext': ext,
                'source_path': source_path,
                'md_path': md_path,
                'filename': filename,
                'folder': folder_display,
                'md_exists': md_exists,
            })

        # Sắp xếp: thư mục gốc trước, rồi theo ABC
        results.sort(key=lambda x: (x['folder'] != '(Thư mục gốc)', x['folder'], x['filename']))

        return jsonify({
            'path': os.path.abspath(folder_path),
            'files': results,
            'total': len(results)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Lỗi khi quét thư mục: {str(e)}'})


@app.route('/api/execute', methods=['POST'])
def execute_convert():
    """Thực thi chuyển đổi các file đã chọn."""
    data = request.get_json()
    folder_path = data.get('path', '')
    indices = data.get('indices', [])

    if not folder_path or not os.path.isdir(folder_path):
        return jsonify({'error': 'Đường dẫn thư mục không hợp lệ.'})
    if not indices:
        return jsonify({'error': 'Không có file nào được chọn.'})

    # Quét lại để có danh sách file
    skip_doc = data.get('skip_doc', False)
    force = data.get('force', False)
    files = scan_directory(folder_path, force=force, skip_doc=skip_doc)

    # Sắp xếp giống như lúc scan
    files_sorted = []
    for ext, source_path, md_path in files:
        filename = os.path.basename(source_path)
        rel_dir = os.path.relpath(os.path.dirname(source_path), folder_path)
        if rel_dir == '.':
            folder_display = '(Thư mục gốc)'
        else:
            folder_display = rel_dir
        files_sorted.append({
            'ext': ext,
            'source_path': source_path,
            'md_path': md_path,
            'filename': filename,
            'folder': folder_display,
        })
    files_sorted.sort(key=lambda x: (x['folder'] != '(Thư mục gốc)', x['folder'], x['filename']))

    # Chọn các file theo indices
    selected = [files_sorted[i] for i in indices if i < len(files_sorted)]

    total = len(selected)
    ok_count = 0
    notext_count = 0
    error_count = 0
    details = []

    for idx, item in enumerate(selected):
        ext = item['ext']
        source_path = item['source_path']
        md_path = item['md_path']
        filename = item['filename']

        # Skip if md already exists and force is False
        if os.path.exists(md_path) and not force:
            details.append({
                'file': filename,
                'md_name': os.path.basename(md_path),
                'status': 'notext',
                'error': 'File .md đã tồn tại (bỏ qua)'
            })
            notext_count += 1
            continue

        if ext == '.docx':
            text = read_docx_text(source_path)
            if text is None:
                details.append({
                    'file': filename,
                    'md_name': os.path.basename(md_path),
                    'status': 'notext',
                    'error': 'Không có nội dung text'
                })
                notext_count += 1
                continue

            try:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                details.append({
                    'file': filename,
                    'md_name': os.path.basename(md_path),
                    'status': 'ok',
                    'chars': len(text),
                    'error': None
                })
                ok_count += 1
            except Exception as e:
                details.append({
                    'file': filename,
                    'md_name': os.path.basename(md_path),
                    'status': 'error',
                    'error': str(e)
                })
                error_count += 1

        elif ext == '.doc':
            try:
                text, error_msg = read_doc_via_win32com(source_path)
            except Exception as e:
                text = None
                error_msg = str(e)

            if error_msg:
                details.append({
                    'file': filename,
                    'md_name': os.path.basename(md_path),
                    'status': 'error',
                    'error': error_msg
                })
                error_count += 1
                continue

            if text is None:
                details.append({
                    'file': filename,
                    'md_name': os.path.basename(md_path),
                    'status': 'notext',
                    'error': 'Không có nội dung text'
                })
                notext_count += 1
                continue

            try:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                details.append({
                    'file': filename,
                    'md_name': os.path.basename(md_path),
                    'status': 'ok',
                    'chars': len(text),
                    'error': None
                })
                ok_count += 1
            except Exception as e:
                details.append({
                    'file': filename,
                    'md_name': os.path.basename(md_path),
                    'status': 'error',
                    'error': str(e)
                })
                error_count += 1

            # Delay nhẹ giữa các file .doc để Word không bị quá tải
            if idx < len(selected) - 1:
                time.sleep(0.5)

    return jsonify({
        'total': total,
        'ok': ok_count,
        'notext': notext_count,
        'errors': error_count,
        'details': details
    })


# ============================================================
# MAIN
# ============================================================

def main():
    host = '127.0.0.1'
    port = 5788

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print('=' * 60)
    print('  DocxToMd - GUI')
    print('=' * 60)
    print(f'  Server dang chay tai: http://{host}:{port}')
    print('  Nhan Ctrl+C de thoat.')
    print('=' * 60)

    def open_browser():
        webbrowser.open(f'http://{host}:{port}')

    threading.Timer(1.5, open_browser).start()

    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    main()