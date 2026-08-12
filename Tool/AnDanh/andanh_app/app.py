import sys
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# ============================================================
# AUTO-INSTALL THƯ VIỆN THIẾU
# ============================================================
def _check_and_install():
    """Tự động cài flask và python-docx nếu chưa có."""
    missing = []
    try:
        import flask
    except ImportError:
        missing.append("flask")
    try:
        import docx
    except ImportError:
        missing.append("python-docx")
    if missing:
        print(f"[SETUP] Thieu thu vien: {', '.join(missing)}. Dang cai dat...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
            stdout=sys.stdout, stderr=sys.stderr
        )
        print("[SETUP] Cai dat thanh cong! Vui long chay lai.")
        sys.exit(0)

_check_and_install()

from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
from offline_server import run_desktop_app
from docx_io import DocxIO
from detector import PIIDetector

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024


# Custom error handlers to return JSON instead of HTML
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File qua lon. Gioi han 50MB.'}), 413

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Yeu cau khong hop le'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Khong tim thay duong dan'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Loi may chu noi bo'}), 500

UPLOAD_FOLDER = tempfile.mkdtemp()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['LAST_DOC'] = None
app.config['LAST_ENTITIES'] = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    if not file.filename.lower().endswith('.docx'):
        return jsonify({'error': 'Only .docx allowed'}), 400

    safe_name = secure_filename(file.filename) or 'document.docx'
    path = os.path.join(app.config['UPLOAD_FOLDER'], f'{uuid.uuid4().hex}_{safe_name}')
    file.save(path)

    doc = DocxIO(path)
    text = doc.get_text()
    detector = PIIDetector(text)
    entities = detector.detect()

    app.config['LAST_DOC'] = path
    app.config['LAST_ENTITIES'] = entities
    return jsonify({'entities': entities})

@app.route('/export', methods=['POST'])
def export():
    data = request.get_json(silent=True) or {}
    replacements = data.get('replacements')
    if replacements is None:
        # Tương thích với giao diện phiên bản cũ.
        replacements = [
            {'old': old, 'new': new}
            for old, new in (data.get('selected') or {}).items()
        ]
    if not isinstance(replacements, list) or len(replacements) > 500:
        return jsonify({'error': 'Danh sách thay thế không hợp lệ'}), 400

    cleaned = []
    seen = set()
    for item in replacements:
        if not isinstance(item, dict):
            continue
        old = str(item.get('old', '')).strip()
        new = str(item.get('new', '')).strip() or '[Ẩn]'
        if not old or len(old) > 500 or len(new) > 500:
            continue
        key = old.casefold()
        if key not in seen:
            seen.add(key)
            cleaned.append((old, new))
    if not cleaned:
        return jsonify({'error': 'Chưa chọn thông tin cần ẩn'}), 400

    path = app.config.get('LAST_DOC')
    if not path or not os.path.exists(path):
        return jsonify({'error': 'No document'}), 400

    doc = DocxIO(path)
    # Cụm dài phải được thay trước để không phá hỏng tên/địa chỉ đầy đủ.
    for old, new in sorted(cleaned, key=lambda pair: len(pair[0]), reverse=True):
        doc.replace_text(old, new)
    fd, out_path = tempfile.mkstemp(suffix='.docx')
    os.close(fd)
    doc.save(out_path)
    response = send_file(out_path, as_attachment=True, download_name='anonymized.docx')

    def cleanup_output():
        try:
            os.remove(out_path)
        except OSError:
            pass

    response.call_on_close(cleanup_output)
    return response

if __name__ == '__main__':
    port = int(os.environ.get('ANDANH_PORT', '5787'))
    
    print("=" * 55)
    print("  Cong cu tu dong an thong tin trong van ban")
    print("=" * 55)
    print("  Nhan Ctrl+C de thoat")
    print("=" * 55)
    run_desktop_app(
        app, 'an-danh-van-ban', preferred_port=port,
        open_browser=(
            os.environ.get('OFFLINE_TOOL_NO_BROWSER') != '1'
            and os.environ.get('ANDANH_NO_BROWSER') != '1'
        ),
    )
