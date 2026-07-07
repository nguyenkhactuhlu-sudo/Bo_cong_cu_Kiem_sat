# -*- coding: utf-8 -*-
"""
PdfToMd GUI - Công cụ chuyển đổi PDF/Ảnh sang Markdown (Web-based GUI)
======================================================================
Flask backend + HTML/JS frontend tích hợp trong 1 file Python.
Sử dụng: python pdf_to_md_gui.py

Chức năng:
  - Nhập Gemini API Key (lưu localStorage)
  - Quét đệ quy thư mục cha, tìm file PDF/Ảnh
  - Hiển thị cây thư mục với danh sách file
  - Chọn/bỏ chọn file để chuyển đổi
  - Gọi Gemini OCR (qua pdf_to_md.py engine) hoặc pypdf free
  - Giữ nguyên file gốc, tạo file .md bên cạnh
"""

import os
import sys
import json
import time
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from flask import Flask, request, jsonify

# ============================================================
# IMPORT ENGINE TỪ pdf_to_md.py (cùng thư mục)
# ============================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from pdf_to_md import (
        convert_file,
        read_pdf_with_pypdf,
        get_pdf_info,
        SUPPORTED_EXTENSIONS,
    )
    ENGINE_AVAILABLE = True
except ImportError as e:
    ENGINE_AVAILABLE = False
    print(f"[WARNING] Không thể import pdf_to_md: {e}. Dùng engine dự phòng.")

SUPPORTED_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif", ".webp"}

app = Flask(__name__, static_folder=None)

# ============================================================
# SCAN DIRECTORY (không phụ thuộc pdf_to_md)
# ============================================================
def scan_directory(root_dir, force=False):
    """Quét đệ quy thư mục, trả về danh sách file PDF/Ảnh."""
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
    """Gọi engine convert_file từ pdf_to_md.py."""
    if ENGINE_AVAILABLE:
        # Override API key bằng cách set env var tạm
        import pdf_to_md as engine
        old_key = engine.GEMINI_API_KEY
        engine.GEMINI_API_KEY = api_key
        try:
            ok, out_path = convert_file(file_path, api_key=api_key,
                                        workers=workers, harmonize=harmonize)
            return ok, out_path
        finally:
            engine.GEMINI_API_KEY = old_key
    else:
        # Fallback: thử pypdf nếu là PDF
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
# HTML TEMPLATE (INLINE)
# ============================================================
HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PdfToMd - Chuyển đổi PDF/Ảnh sang Markdown</title>
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

        /* API KEY */
        .apikey-row {
            display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
            margin-bottom: 16px; padding-bottom: 16px;
            border-bottom: 1px dashed var(--border);
        }
        .apikey-input {
            flex: 1; min-width: 280px; padding: 11px 14px;
            border: 2px solid var(--border); border-radius: 10px;
            font-size: 13px; font-family: monospace; background: var(--gray-bg); color: #333;
            transition: border-color 0.2s;
        }
        .apikey-input:focus { outline: none; border-color: var(--bronze); background: #fff; }
        .apikey-status {
            font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 6px;
            flex-shrink: 0;
        }
        .apikey-status.saved { background: var(--green-light); color: var(--green); }
        .apikey-status.empty { background: #fff3e0; color: var(--orange); }
        .apikey-hint {
            font-size: 12px; color: #888; margin-top: 2px;
        }
        .apikey-hint a {
            color: var(--sky-dark); font-weight: 600; text-decoration: underline;
        }

        /* FOLDER */
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
        .option-label select {
            padding: 5px 10px; border-radius: 6px; border: 1px solid var(--border);
            font-family: inherit; font-size: 13px; cursor: pointer;
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
        .btn-save-key {
            color: #fff; background: linear-gradient(135deg, #4caf50, #2e7d32);
            box-shadow: 0 4px 12px rgba(46,125,50,0.25);
        }
        .btn-save-key:hover { transform: translateY(-2px); }

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
        .file-icon.pdf { color: var(--red); }
        .file-icon.image { color: var(--sky); }
        .file-icon.has-md { color: var(--green); }
        .file-name { font-weight: 500; min-width: 0; word-break: break-all; flex: 1; }
        .file-name.has-md-name { color: #999; text-decoration: line-through; }
        .file-ext {
            font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px;
            flex-shrink: 0; margin-left: 8px;
        }
        .file-ext.pdf { background: var(--red-light); color: var(--red); }
        .file-ext.image { background: #e3f2fd; color: var(--sky-dark); }
        .file-md-status {
            font-size: 11px; flex-shrink: 0; margin-left: 8px;
            padding: 2px 8px; border-radius: 4px;
        }
        .file-md-status.exists { background: var(--green-light); color: var(--green); }
        .file-md-status.new { background: #f5f5f5; color: #999; }
        .file-size {
            font-size: 11px; color: #aaa; flex-shrink: 0; margin-left: 4px;
            min-width: 55px; text-align: right;
        }

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
        .result-summary .error-detail { color: var(--red); }

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
            max-width: 450px; width: 90%;
        }
        .progress-box .spinner {
            width: 40px; height: 40px; border: 4px solid #e0e0e0;
            border-top-color: var(--sky-dark); border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 14px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .progress-box p { font-weight: 600; color: var(--sky-dark); }
        .progress-box .progress-text { font-size: 12px; color: #999; margin-top: 6px; }

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
            .apikey-row { flex-direction: column; }
            .apikey-row .btn { width: 100%; justify-content: center; }
            .action-bar { gap: 6px; }
            .options-row { flex-direction: column; gap: 10px; }
        }
    </style>
</head>
<body>
    <!-- HEADER -->
    <div class="header">
        <div class="header-icon"><i class="fas fa-file-pdf"></i></div>
        <div>
            <div class="header-title">PdfToMd - <span>Chuyển đổi PDF/Ảnh sang Markdown</span></div>
            <div class="header-sub"><i class="fas fa-robot"></i> Gemini OCR + pypdf — Hàng loạt, tự động</div>
        </div>
    </div>

    <!-- MAIN -->
    <div class="main-content">
        <!-- STEP 0: API Key -->
        <div class="step-card" id="step0">
            <h2><span class="step-num">0</span> <i class="fas fa-key"></i> Nhập Gemini API Key</h2>
            <p style="color:#777;font-size:13px;margin-bottom:10px;">
                Cần Gemini API Key để OCR file PDF scan và ảnh. 
                Lấy key miễn phí tại 
                <a href="https://aistudio.google.com/apikey" target="_blank" style="color:var(--sky-dark);font-weight:600;">
                    Google AI Studio <i class="fas fa-external-link-alt"></i>
                </a>
            </p>
            <div class="apikey-row">
                <input type="password" class="apikey-input" id="apiKeyInput" 
                    placeholder="Dán Gemini API Key vào đây (VD: AIza...)" />
                <button class="btn btn-save-key" onclick="saveApiKey()">
                    <i class="fas fa-save"></i> Lưu API Key
                </button>
                <button class="btn btn-outline" onclick="toggleKeyVisibility()" title="Hiện/ẩn key">
                    <i class="fas fa-eye" id="toggleKeyIcon"></i>
                </button>
                <span class="apikey-status empty" id="apikeyStatus">Chưa có key</span>
            </div>
            <p class="apikey-hint" id="apikeyHint">API Key được lưu trong bộ nhớ trình duyệt (localStorage).</p>
        </div>

        <!-- STEP 1: Chọn thư mục -->
        <div class="step-card" id="step1">
            <h2><span class="step-num">1</span> <i class="fas fa-folder-open"></i> Chọn thư mục cần quét</h2>
            <p style="color:#777;font-size:13px;margin-bottom:12px;">
                Chọn thư mục cha chứa các file PDF/Ảnh. Tool sẽ tự động quét tất cả 
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
                <label class="option-label" title="Ghi đè file .md nếu đã tồn tại">
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
                    <p class="progress-text" id="progressSub"></p>
                </div>
            </div>

            <!-- Toast -->
            <div class="toast" id="toast"></div>

            <!-- Cấu hình -->
            <div class="options-row" style="margin-top:0;padding-top:0;border-top:none;margin-bottom:16px;">
                <label class="option-label" title="Số request đồng thời gửi lên Gemini API">
                    <i class="fas fa-bolt" style="color:var(--bronze);"></i> Workers:
                    <select id="optWorkers">
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3" selected>3</option>
                        <option value="4">4</option>
                        <option value="5">5</option>
                    </select>
                </label>
                <label class="option-label" title="Chuẩn hóa Markdown sau khi OCR (tăng chất lượng)">
                    <input type="checkbox" id="optHarmonize" />
                    <i class="fas fa-magic" style="color:var(--plum-light);"></i> Harmonize (chuẩn hóa Markdown)
                </label>
            </div>

            <!-- Stats -->
            <div class="stats-row" id="statsRow" style="display:none;">
                <span class="stat-badge info" id="statTotal">0 file tìm thấy</span>
                <span class="stat-badge success" id="statPdf">0 PDF</span>
                <span class="stat-badge orange" id="statImg">0 Ảnh</span>
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
                <p>Không tìm thấy file PDF/Ảnh nào cần chuyển đổi!</p>
                <p style="font-size:13px;">Tất cả file đã có .md hoặc không có file hỗ trợ trong thư mục.</p>
            </div>
        </div>

        <!-- Thông tin -->
        <div class="step-card">
            <h2><i class="fas fa-info-circle"></i> Thông tin & cách sử dụng</h2>
            <ul style="list-style:none;padding:0;">
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 0:</strong> Nhập Gemini API Key (lấy miễn phí từ Google AI Studio)</span>
                </li>
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 1:</strong> Chọn thư mục cha chứa file PDF/Ảnh (tool tự quét cả thư mục con)</span>
                </li>
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 2:</strong> Xem danh sách file hiển thị theo cây thư mục</span>
                </li>
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 3:</strong> Tích chọn file muốn chuyển đổi</span>
                </li>
                <li style="padding:6px 0;font-size:14px;display:flex;align-items:flex-start;gap:8px;">
                    <i class="fas fa-check-circle" style="color:var(--bronze);margin-top:2px;"></i>
                    <span><strong>Bước 4:</strong> Bấm "Thực thi chuyển đổi" để tạo file .md bên cạnh file gốc</span>
                </li>
            </ul>
            <div class="dev-info">
                <p><i class="fas fa-cog"></i> Engine: <strong>Gemini 2.5 Flash API + pypdf fallback</strong> — OCR PDF/Ảnh sang Markdown</p>
                <p><i class="fas fa-shield-alt"></i> An toàn: <strong>File gốc được giữ nguyên</strong> — Chỉ tạo thêm file .md bên cạnh</p>
                <p><i class="fas fa-info-circle"></i> PDF có text: dùng <strong>pypdf (nhanh, miễn phí)</strong>. PDF scan/ảnh: gọi <strong>Gemini API</strong>.</p>
                <p><i class="fas fa-file"></i> Hỗ trợ: <strong>.pdf, .jpg, .jpeg, .png, .tiff, .tif, .bmp, .gif, .webp</strong></p>
                <p><i class="fas fa-user"></i> Phát triển bởi: <strong>Nguyễn Khắc Tú</strong></p>
                <p><i class="fas fa-building"></i> Đơn vị: <strong>Viện KSND khu vực 5 - Bắc Ninh</strong></p>
            </div>
            <div class="note-box">
                <i class="fas fa-lightbulb"></i>
                <p><strong>Lưu ý:</strong> Công cụ <strong>giữ nguyên file gốc</strong>, chỉ tạo thêm file .md bên cạnh. File PDF scan/ảnh sẽ gọi Gemini API (tốn token, có giới hạn rate limit). File PDF có text sẽ dùng pypdf (nhanh, miễn phí). Mỗi file upload lên Gemini không quá 20MB.</p>
            </div>
        </div>
    </div>

    <script>
        // ============ API KEY MANAGEMENT ============
        function getApiKey() {
            return localStorage.getItem('pdf_to_md_api_key') || '';
        }

        function saveApiKey() {
            var key = document.getElementById('apiKeyInput').value.trim();
            if (!key) {
                showToast('Vui lòng nhập API Key.', 'error');
                return;
            }
            localStorage.setItem('pdf_to_md_api_key', key);
            document.getElementById('apiKeyInput').value = '';
            updateApiKeyStatus();
            showToast('API Key đã được lưu thành công!', 'success');
        }

        function updateApiKeyStatus() {
            var key = getApiKey();
            var statusEl = document.getElementById('apikeyStatus');
            var inputEl = document.getElementById('apiKeyInput');
            if (key) {
                var masked = key.substring(0, 8) + '...' + key.substring(key.length - 4);
                statusEl.textContent = 'Đã lưu: ' + masked;
                statusEl.className = 'apikey-status saved';
                inputEl.placeholder = 'Đã lưu API Key. Nhập key mới để thay đổi.';
            } else {
                statusEl.textContent = 'Chưa có key';
                statusEl.className = 'apikey-status empty';
                inputEl.placeholder = 'Dán Gemini API Key vào đây (VD: AIza...)';
            }
        }

        function toggleKeyVisibility() {
            var input = document.getElementById('apiKeyInput');
            var icon = document.getElementById('toggleKeyIcon');
            if (input.type === 'password') {
                input.type = 'text';
                icon.className = 'fas fa-eye-slash';
            } else {
                input.type = 'password';
                icon.className = 'fas fa-eye';
            }
        }

        // ============ STATE ============
        var scanData = null;
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
            var force = document.getElementById('optForce').checked;

            showProgress('Đang quét thư mục...');
            fetch('/api/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: path, force: force})
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
            var totalPdf = 0, totalImg = 0;
            for (var i = 0; i < data.files.length; i++) {
                if (data.files[i].ext === '.pdf') totalPdf++;
                else totalImg++;
            }
            document.getElementById('statTotal').innerHTML = '<i class="fas fa-file"></i> ' + data.files.length + ' file tìm thấy';
            document.getElementById('statPdf').innerHTML = '<i class="fas fa-file-pdf"></i> ' + totalPdf + ' PDF';
            document.getElementById('statImg').innerHTML = '<i class="fas fa-image"></i> ' + totalImg + ' Ảnh';

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
                    var isPdf = f.ext === '.pdf';
                    var hasMd = f.md_exists;

                    html += '<div class="file-row">';
                    html += '<input type="checkbox" id="' + cbId + '" ' + (hasMd ? '' : 'checked') + ' data-idx="' + fileIdx + '" data-folder="' + escHtml(fname) + '" onchange="updateStats()" />';

                    // Icon
                    if (hasMd) {
                        html += '<i class="fas fa-check-circle file-icon has-md" title="Đã có file .md"></i>';
                    } else if (isPdf) {
                        html += '<i class="fas fa-file-pdf file-icon pdf" title="File PDF"></i>';
                    } else {
                        html += '<i class="fas fa-image file-icon image" title="File ảnh"></i>';
                    }

                    // Name
                    html += '<span class="file-name' + (hasMd ? ' has-md-name' : '') + '" title="' + escHtml(f.filename) + '">' + escHtml(f.filename) + '</span>';

                    // File size
                    if (f.size_mb !== undefined) {
                        var sizeClass = f.size_mb > 15 ? ' style="color:var(--red);font-weight:600;"' : '';
                        html += '<span class="file-size"' + sizeClass + '>' + f.size_mb.toFixed(1) + ' MB</span>';
                    }

                    // Extension badge
                    var extClass = isPdf ? 'pdf' : 'image';
                    html += '<span class="file-ext ' + extClass + '">' + f.ext + '</span>';

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
            var div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
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
            var apiKey = getApiKey();
            if (!apiKey) {
                showToast('Vui lòng nhập API Key ở Bước 0 trước!', 'error');
                document.getElementById('step0').scrollIntoView({behavior: 'smooth'});
                return;
            }
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

            var workers = parseInt(document.getElementById('optWorkers').value) || 3;
            var harmonize = document.getElementById('optHarmonize').checked;

            var hasPdfFiles = false;
            for (var i = 0; i < selectedIndices.length; i++) {
                if (scanData.files[selectedIndices[i]].ext === '.pdf') {
                    hasPdfFiles = true;
                    break;
                }
            }

            var confirmMsg = 'Bạn có CHẮC CHẮN muốn chuyển đổi ' + selectedIndices.length + ' file đã chọn?\n\n' +
                'File .md sẽ được tạo cùng thư mục với file gốc.\n' +
                'File gốc sẽ được GIỮ NGUYÊN.\n\n';
            if (hasPdfFiles) {
                confirmMsg += 'PDF có text → dùng pypdf (nhanh, miễn phí)\n';
            }
            confirmMsg += 'PDF scan / Ảnh → gọi Gemini API (tốn token)\n';
            confirmMsg += '\nWorkers: ' + workers + ' | Harmonize: ' + (harmonize ? 'Bật' : 'Tắt');
            confirmMsg += '\n\nBấm OK để tiếp tục.';

            if (!confirm(confirmMsg)) {
                return;
            }

            var resultSummary = document.getElementById('resultSummary');
            resultSummary.innerHTML = '';

            // Convert tuần tự từng file qua API
            showProgress('Đang chuyển đổi 0/' + selectedIndices.length + ' file...', 'Chuẩn bị...');
            document.getElementById('btnExecute').disabled = true;

            var okCount = 0, failCount = 0, skipCount = 0;
            var details = [];

            function convertNext(idx) {
                if (idx >= selectedIndices.length) {
                    // Done
                    hideProgress();
                    document.getElementById('btnExecute').disabled = false;
                    showExecuteResult(okCount, failCount, skipCount, details);
                    return;
                }

                var fileIdx = selectedIndices[idx];
                var file = scanData.files[fileIdx];
                var current = idx + 1;
                var total = selectedIndices.length;

                updateProgress(
                    'Đang chuyển đổi ' + current + '/' + total + ' file...',
                    file.filename
                );

                fetch('/api/convert', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        file_path: file.source_path,
                        api_key: apiKey,
                        workers: workers,
                        harmonize: harmonize
                    })
                })
                .then(r => r.json())
                .then(d => {
                    if (d.ok) {
                        okCount++;
                        details.push({file: file.filename, md: d.md_name, status: 'ok', chars: d.chars, method: d.method});
                    } else {
                        failCount++;
                        details.push({file: file.filename, status: 'fail', error: d.error || 'Không xác định'});
                    }
                    // Tiếp tục file tiếp theo
                    setTimeout(function() { convertNext(idx + 1); }, 500);
                })
                .catch(e => {
                    failCount++;
                    details.push({file: file.filename, status: 'fail', error: String(e)});
                    setTimeout(function() { convertNext(idx + 1); }, 500);
                });
            }

            convertNext(0);
        }

        function showExecuteResult(ok, fail, skip, details) {
            var resultSummary = document.getElementById('resultSummary');
            var html = '<div class="result-summary">';
            html += '<h3><i class="fas fa-clipboard-check"></i> Kết quả chuyển đổi</h3>';
            html += '<p><strong>Tổng số file đã chọn:</strong> ' + (ok + fail + skip) + '</p>';
            html += '<p style="color:var(--green);"><strong>Đã chuyển đổi thành công:</strong> ' + ok + '</p>';
            if (fail > 0) {
                html += '<p class="error-detail"><strong>Lỗi:</strong> ' + fail + '</p>';
            }
            if (details && details.length > 0) {
                html += '<div style="margin-top:10px;max-height:300px;overflow-y:auto;font-size:12px;">';
                for (var i = 0; i < details.length; i++) {
                    var det = details[i];
                    if (det.status === 'ok') {
                        html += '<p style="margin:3px 0;color:var(--green);">' +
                            '<i class="fas fa-check-circle"></i> ' + escHtml(det.file) +
                            ' → ' + escHtml(det.md) +
                            ' (' + (det.chars||0) + ' chars' + (det.method ? ', ' + det.method : ')' + ')</p>';
                    } else {
                        html += '<p style="margin:3px 0;color:var(--red);">' +
                            '<i class="fas fa-times-circle"></i> ' + escHtml(det.file) +
                            ' — ' + escHtml(det.error || 'Lỗi') + '</p>';
                    }
                }
                html += '</div>';
            }
            html += '</div>';
            resultSummary.innerHTML = html;
            resultSummary.scrollIntoView({behavior: 'smooth'});

            if (ok > 0) {
                showToast('Đã chuyển đổi thành công ' + ok + ' file!', 'success');
            }
        }

        // ============ UI HELPERS ============
        function showToast(msg, type) {
            var t = document.getElementById('toast');
            t.className = 'toast ' + (type || 'info');
            t.textContent = msg;
            t.style.display = 'flex';
            clearTimeout(t._timeout);
            t._timeout = setTimeout(function() { t.style.display = 'none'; }, 5000);
        }

        function showProgress(msg, sub) {
            document.getElementById('progressText').textContent = msg || 'Đang xử lý...';
            document.getElementById('progressSub').textContent = sub || '';
            document.getElementById('progressOverlay').classList.add('active');
        }

        function updateProgress(msg, sub) {
            document.getElementById('progressText').textContent = msg || '';
            document.getElementById('progressSub').textContent = sub || '';
        }

        function hideProgress() {
            document.getElementById('progressOverlay').classList.remove('active');
        }

        // Enter key to scan
        document.getElementById('folderPath').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') scanFolder();
        });

        // ============ INIT ============
        updateApiKeyStatus();
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
    """Mở hộp thoại chọn thư mục bằng tkinter."""
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder = filedialog.askdirectory(title='Chọn thư mục cha chứa file PDF/Ảnh')
        root.destroy()
        if folder:
            folder = os.path.normpath(folder)
        return jsonify({'path': folder or ''})
    except Exception as e:
        return jsonify({'path': '', 'error': str(e)})


@app.route('/api/scan', methods=['POST'])
def scan_folder():
    """Quét thư mục và trả về danh sách file PDF/Ảnh."""
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


@app.route('/api/convert', methods=['POST'])
def convert_single():
    """Chuyển đổi 1 file PDF/Ảnh sang Markdown."""
    data = request.get_json()
    file_path = data.get('file_path', '')
    api_key = data.get('api_key', '')
    workers = int(data.get('workers', 3))
    harmonize = data.get('harmonize', False)

    if not file_path or not os.path.isfile(file_path):
        return jsonify({'ok': False, 'error': 'File không tồn tại'})
    if not api_key:
        return jsonify({'ok': False, 'error': 'Thiếu API Key'})

    try:
        ok, out_path = convert_file_local(file_path, api_key,
                                          workers=workers, harmonize=harmonize)
        if ok and out_path:
            md_name = os.path.basename(out_path)
            chars = 0
            method = 'pypdf'
            if os.path.exists(out_path):
                with open(out_path, 'r', encoding='utf-8') as f:
                    chars = len(f.read())
            # Kiểm tra xem có dùng Gemini không
            ext = Path(file_path).suffix.lower()
            if ext != '.pdf' or not read_pdf_with_pypdf(file_path):
                method = 'Gemini API'
            return jsonify({
                'ok': True,
                'md_name': md_name,
                'chars': chars,
                'method': method
            })
        else:
            return jsonify({'ok': False, 'error': 'Không thể chuyển đổi file này'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)})


# ============================================================
# MAIN
# ============================================================
def main():
    import socket

    def find_free_port(start=5000):
        for port in range(start, 5100):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(('127.0.0.1', port))
                s.close()
                return port
            except OSError:
                continue
        return 5000

    port = find_free_port(5100)

    print("=" * 60)
    print("  PdfToMd GUI - Chuyển đổi PDF/Ảnh sang Markdown")
    print("=" * 60)
    print(f"  Server: http://127.0.0.1:{port}")
    print(f"  Nhấn Ctrl+C để thoát")
    print("=" * 60)

    webbrowser.open(f"http://127.0.0.1:{port}")

    app.run(host='127.0.0.1', port=port, debug=False, threaded=True)


if __name__ == '__main__':
    main()