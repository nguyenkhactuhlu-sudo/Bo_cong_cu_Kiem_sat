"""
OCR PDF Tool - Configuration Module (Flask Web App)
Chứa tất cả các hằng số, đường dẫn và cấu hình cho ứng dụng.
"""

import os
import sys

# ── Đường dẫn gốc ─────────────────────────────────────────────
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = SOURCE_DIR

# ── Đường dẫn Tesseract ───────────────────────────────────────
# When frozen (PyInstaller): Tesseract-OCR is in same folder as EXE
# When developing in this repository, reuse the copied portable Tesseract runtime.
if getattr(sys, 'frozen', False):
    TESSERACT_DIR = os.path.join(BASE_DIR, "Tesseract-OCR")
else:
    TESSERACT_DIR = os.path.join(
        os.path.dirname(BASE_DIR), "OCR_PDF_Tool", "Tesseract-OCR"
    )
TESSERACT_EXE = os.path.join(TESSERACT_DIR, "tesseract.exe")
TESSDATA_DIR = os.path.join(TESSERACT_DIR, "tessdata")

# ── Thư mục tạm ───────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    TEMP_DIR = os.path.join(BASE_DIR, "temp_images")
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
else:
    TEMP_DIR = os.path.join(BASE_DIR, "temp_images")
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# ── Ngôn ngữ OCR ──────────────────────────────────────────────
OCR_LANGUAGES = {
    "Tiếng Việt": "vie",
    "Việt + Anh": "vie+eng",
}
DEFAULT_LANGUAGE = "Tiếng Việt"

# ── Định dạng đầu ra ──────────────────────────────────────────
OUTPUT_FORMATS = {
    ".docx (Word)": "docx",
    ".md (Markdown)": "md",
    ".txt (Text)": "txt",
}
DEFAULT_FORMAT = ".docx (Word)"

# ── Cấu hình Tesseract ────────────────────────────────────────
TESSERACT_PSM = 6
TESSERACT_OEM = 3
PDF_RENDER_DPI = 300
IMAGE_FORMAT = "png"

# ── Cấu hình Word ─────────────────────────────────────────────
DOCX_FONT_NAME = "Times New Roman"
DOCX_FONT_SIZE = 13

# ── Cấu hình Flask ────────────────────────────────────────────
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5791
APP_TITLE = "PHẦN MỀM TỰ ĐỘNG CHUYỂN ĐỔI PDF SANG WORD/MARKDOWN/TEXT"
APP_VERSION = "1.0.0"

# ── Hàm tiện ích ──────────────────────────────────────────────
def get_tesseract_version():
    """Trả về phiên bản Tesseract nếu có."""
    try:
        import subprocess
        options = {}
        if os.name == "nt":
            startup = subprocess.STARTUPINFO()
            startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = subprocess.SW_HIDE
            options = {"creationflags": subprocess.CREATE_NO_WINDOW, "startupinfo": startup}
        result = subprocess.run(
            [TESSERACT_EXE, "--version"],
            capture_output=True, text=True, timeout=10, **options
        )
        return result.stdout.split("\n")[0] if result.returncode == 0 else "Unknown"
    except Exception:
        return "Unknown"

def ensure_dirs():
    """Đảm bảo các thư mục cần thiết tồn tại."""
    for d in [TEMP_DIR, UPLOAD_DIR, OUTPUT_DIR]:
        os.makedirs(d, exist_ok=True)

def cleanup_temp_dir():
    """Dọn dẹp thư mục tạm."""
    import shutil
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
