"""
OCR PDF Tool - Flask Web App (Neubrutalism UI)
Khởi chạy Flask server + tự động mở browser.
"""

import os
import sys
import json
import uuid
import shutil
import zipfile
from io import BytesIO

# Thêm thư mục hiện tại vào path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_file
from offline_server import run_desktop_app

from config import (
    APP_TITLE, APP_VERSION, FLASK_HOST, FLASK_PORT,
    OCR_LANGUAGES, OUTPUT_FORMATS, DEFAULT_LANGUAGE, DEFAULT_FORMAT,
    UPLOAD_DIR, OUTPUT_DIR, ensure_dirs, cleanup_temp_dir,
    get_tesseract_version,
)
from ocr_engine import OCREngine
from pdf_processor import PDFProcessor
from output_generator import OutputGenerator

# ── Init ────────────────────────────────────────────────────
ensure_dirs()

# Fix paths for PyInstaller frozen mode
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    template_dir = os.path.join(base_path, 'templates')
    static_dir = os.path.join(base_path, 'static')
else:
    template_dir = 'templates'
    static_dir = 'static'

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max

# ── Routes ──────────────────────────────────────────────────

@app.route('/')
def index():
    """Giao diện chính."""
    return render_template('index.html',
        title=APP_TITLE,
        version=APP_VERSION,
        languages=list(OCR_LANGUAGES.keys()),
        formats=list(OUTPUT_FORMATS.keys()),
        default_lang=DEFAULT_LANGUAGE,
        default_fmt=DEFAULT_FORMAT,
    )

@app.route('/api/ocr', methods=['POST'])
def process_ocr():
    """API nhận file PDF, chạy OCR, trả về kết quả."""
    if 'file' not in request.files:
        return jsonify({"error": "Vui lòng chọn file PDF."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Vui lòng chọn file."}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Chỉ hỗ trợ file PDF."}), 400

    # Lưu file upload
    file_id = str(uuid.uuid4())[:8]
    filename = f"{file_id}_{file.filename}"
    upload_path = os.path.join(UPLOAD_DIR, filename)
    file.save(upload_path)

    # Đọc params
    lang_key = request.form.get('language', DEFAULT_LANGUAGE)
    fmt_key = request.form.get('format', DEFAULT_FORMAT)
    lang_code = OCR_LANGUAGES.get(lang_key, 'vie')
    output_fmt = OUTPUT_FORMATS.get(fmt_key, 'docx')

    try:
        # OCR xử lý
        engine = OCREngine(lang_code)
        pdf_proc = PDFProcessor(upload_path)
        total = pdf_proc.get_page_count()
        fname = pdf_proc.get_file_name()

        pages_text = []
        for i in range(total):
            img = pdf_proc.render_page(i)
            base = img.replace(".png", "").replace(".jpg", "")
            text = engine.ocr_image(img, base)
            pages_text.append(text)
            try:
                os.remove(img)
            except OSError:
                pass

        pdf_proc.close()
        cleanup_temp_dir()

        # Tạo output
        gen = OutputGenerator(fname, OUTPUT_DIR)
        output_path = gen.generate(pages_text, output_fmt)

        # Dọn file upload
        try:
            os.remove(upload_path)
        except OSError:
            pass

        return jsonify({
            "success": True,
            "output_file": os.path.basename(output_path),
            "output_path": output_path,
            "total_pages": total,
            "pages_text": pages_text,
        })

    except Exception as e:
        try:
            os.remove(upload_path)
        except OSError:
            pass
        cleanup_temp_dir()
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<filename>')
def download_file(filename):
    """Tải file kết quả."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File không tồn tại."}), 404
    return send_file(filepath, as_attachment=True)

@app.route('/api/ocr/batch', methods=['POST'])
def process_ocr_batch():
    """API nhận nhiều file PDF, chạy OCR tuần tự, trả về kết quả."""
    if 'files' not in request.files:
        return jsonify({"error": "Vui lòng chọn ít nhất 1 file PDF."}), 400

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "Vui lòng chọn ít nhất 1 file."}), 400

    # Đọc params
    lang_key = request.form.get('language', DEFAULT_LANGUAGE)
    fmt_key = request.form.get('format', DEFAULT_FORMAT)
    lang_code = OCR_LANGUAGES.get(lang_key, 'vie')
    output_fmt = OUTPUT_FORMATS.get(fmt_key, 'docx')

    results = []
    errors = []

    def process_one_file(file):
        """Xử lý 1 file PDF, trả về dict kết quả."""
        if not file.filename.lower().endswith('.pdf'):
            return {"filename": file.filename, "error": "Không phải file PDF."}

        file_id = str(uuid.uuid4())[:8]
        filename = f"{file_id}_{file.filename}"
        upload_path = os.path.join(UPLOAD_DIR, filename)
        file.save(upload_path)

        try:
            engine = OCREngine(lang_code)
            pdf_proc = PDFProcessor(upload_path)
            total = pdf_proc.get_page_count()
            fname = pdf_proc.get_file_name()

            pages_text = []
            for i in range(total):
                img = pdf_proc.render_page(i)
                base = img.replace(".png", "").replace(".jpg", "")
                text = engine.ocr_image(img, base)
                pages_text.append(text)
                try:
                    os.remove(img)
                except OSError:
                    pass

            pdf_proc.close()
            cleanup_temp_dir()

            gen = OutputGenerator(fname, OUTPUT_DIR)
            output_path = gen.generate(pages_text, output_fmt)

            return {
                "filename": file.filename,
                "success": True,
                "output_file": os.path.basename(output_path),
                "total_pages": total,
                "pages_text": pages_text,
            }
        except Exception as e:
            return {"filename": file.filename, "error": str(e)}
        finally:
            try:
                os.remove(upload_path)
            except OSError:
                pass

    # Xử lý tuần tự từng file
    for f in files:
        if f.filename == '':
            continue
        result = process_one_file(f)
        if result.get("success"):
            results.append(result)
        else:
            errors.append(result)

    return jsonify({
        "success": True,
        "total_files": len(files),
        "processed": len(results),
        "errors": len(errors),
        "results": results,
        "error_list": errors,
    })

@app.route('/api/batch/download', methods=['POST'])
def download_batch_zip():
    """Tải tất cả output thành file ZIP."""
    data = request.get_json()
    if not data or 'files' not in data:
        return jsonify({"error": "Thiếu danh sách file."}), 400

    file_list = data['files']
    memory_zip = BytesIO()
    with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in file_list:
            fpath = os.path.join(OUTPUT_DIR, fname)
            if os.path.exists(fpath):
                zf.write(fpath, fname)

    memory_zip.seek(0)
    return send_file(
        memory_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name='batch_ocr_results.zip'
    )

@app.route('/api/status')
def status():
    """Kiểm tra trạng thái server."""
    return jsonify({
        "languages": list(OCR_LANGUAGES.keys()),
        "formats": list(OUTPUT_FORMATS.keys()),
    })

def main():
    """Hàm chính."""
    # Reconfigure stdout for UTF-8 to support Vietnamese characters
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print("")
    print(f"  ==========================================")
    print(f"  | {APP_TITLE} v{APP_VERSION}")

    print(f"  ==========================================")
    print("")
    print(f"  Dang mo trinh duyet...")
    print(f"  Nhan Ctrl+C de thoat")
    print("")

    run_desktop_app(
        app, 'ocr-pdf-tesseract', preferred_port=FLASK_PORT,
        host=FLASK_HOST,
        open_browser=os.environ.get('OFFLINE_TOOL_NO_BROWSER') != '1',
    )


if __name__ == "__main__":
    main()
