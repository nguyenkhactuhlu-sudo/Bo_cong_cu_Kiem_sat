"""Kiểm tra các trạng thái UI mặc định và chữ ký giữa nguồn gốc/payload."""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
STAGE = Path(__file__).resolve().parent / "stage" / "payload"


def read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


for root, label in ((ROOT, "gốc"), (STAGE, "desktop")):
    interest = read(root, "Tool/App_tinh_lai_suat/index.html")
    if '.law-sidebar-container { display:none' not in interest or '.time-sidebar-container { display:none' not in interest:
        raise SystemExit(f"Tính lãi suất {label} không mặc định đóng panel phụ.")
    if "header-tool-actions" not in interest or "toggleLawBtnTop" not in interest or "toggleTimeBtnTop" not in interest:
        raise SystemExit(f"Tính lãi suất {label} thiếu nút tiện ích top bar.")
    if "cloneNode" in interest or "innerHTML = document" in interest:
        raise SystemExit(f"Tính lãi suất {label} có nguy cơ tái tạo form và mất dữ liệu.")

    court_fee = read(root, "Tool/App_DS/index.html")
    for marker in ("height: 130px", "header-inner", "header-watermark", "margin: 150px auto 20px"):
        if marker not in court_fee:
            raise SystemExit(f"Tính án phí {label} chưa đồng bộ topbar với công cụ tính lãi suất: {marker}")

    deadline = read(root, "Data/TinhTuoiThoiHan.html")
    if deadline.count("legal-note") < 3 or deadline.count("legal-toggle") < 4:
        raise SystemExit(f"Tính thời hạn {label} thiếu nút căn cứ pháp lý.")
    if deadline.count("legal-note-tamgiu collapsed") != 1 or deadline.count("legal-note-tamgiam collapsed") != 1 or deadline.count("legal-note-thoihan collapsed") != 1:
        raise SystemExit(f"Tính thời hạn {label} không mặc định đóng đủ ba căn cứ pháp lý.")

tool_sources = (
    "Tool/App_tinh_lai_suat/index.html",
    "Tool/App_DS/index.html",
    "Data/TinhTuoiThoiHan.html",
    "Tool/AnDanh/andanh_app/templates/index.html",
    "Tool/FileRenamer/file_renamer_gui.py",
    "Tool/SpellChecker/app.py",
    "Tool/OCR_PDF_Tool/source/templates/index.html",
)
for root, label in ((ROOT, "gốc"), (STAGE, "desktop")):
    for relative in tool_sources:
        text = read(root, relative)
        if "Phát triển bởi" in text or "Phối hợp phát triển" in text or "Nguyễn Khắc Tú" in text or "Trần Huy" in text:
            raise SystemExit(f"Công cụ con {label} còn chữ ký: {relative}")

launcher = (Path(__file__).resolve().parent / "main.py").read_text(encoding="utf-8")
if launcher.count("Phát triển bởi:") != 1 or "privacy-notice" not in launcher:
    raise SystemExit("Bảng điều hành desktop phải có đúng một chữ ký và thông báo cục bộ riêng.")
if 'url("/static/lotus.png")' not in launcher or 'launcher_static' not in launcher:
    raise SystemExit("Bảng điều hành desktop chưa dùng nền hoa sen cục bộ.")
dashboard = read(ROOT, "index.html")
if dashboard.count("Phát triển bởi:") != 1 or 'class="footer-logo"' not in dashboard:
    raise SystemExit("Bảng điều hành gốc phải có đúng một chữ ký và logo footer riêng.")
if "display: flex; align-items: center; justify-content: center" not in dashboard or "white-space: nowrap" not in dashboard:
    raise SystemExit("Chữ ký bảng điều hành gốc chưa khóa chữ và logo trên cùng một dòng.")
if "url('static/lotus.png')" not in dashboard or "#dashboard-page::before" not in dashboard:
    raise SystemExit("Bảng điều hành gốc chưa dùng nền hoa sen ở chân trang.")
anonymizer_download = read(ROOT, "Tool/AnDanh/index.html")
if "TẢI XUỐNG CÔNG CỤ" not in anonymizer_download or "KHỞI CHẠY CÔNG CỤ" in anonymizer_download:
    raise SystemExit("Trang tải công cụ che thông tin chưa hiển thị đúng hành động tải xuống.")
renamer = read(STAGE, "Tool/FileRenamer/file_renamer_gui.py")
if "window.pywebview.api.choose_folder" not in renamer:
    raise SystemExit("Bản desktop đổi tên file chưa dùng hộp thoại chọn thư mục native.")

print("OK UI behavior: panel phụ đóng, tool con không có chữ ký, launcher có đúng một chữ ký và thông báo riêng")
