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
    if 'type="date"' in interest or interest.count('placeholder="Ngày/Tháng/Năm"') != 6:
        raise SystemExit(f"Tính lãi suất {label} chưa khóa đủ ô ngày theo thứ tự Ngày/Tháng/Năm.")
    for marker in ("function parseDate", "function formatDmyInput", "function validateDmyInput", "function dateInputToIso"):
        if marker not in interest:
            raise SystemExit(f"Tính lãi suất {label} thiếu bộ chuẩn hóa ngày: {marker}")

    court_fee = read(root, "Tool/App_DS/index.html")
    for marker in ("height: 130px", "header-inner", "header-watermark", "margin: 150px auto 20px"):
        if marker not in court_fee:
            raise SystemExit(f"Tính án phí {label} chưa đồng bộ topbar với công cụ tính lãi suất: {marker}")

    deadline = read(root, "Data/TinhTuoiThoiHan.html")
    if deadline.count("legal-note") < 3 or deadline.count("legal-toggle") < 4:
        raise SystemExit(f"Tính thời hạn {label} thiếu nút căn cứ pháp lý.")
    if deadline.count("legal-note-tamgiu collapsed") != 1 or deadline.count("legal-note-tamgiam collapsed") != 1 or deadline.count("legal-note-thoihan collapsed") != 1:
        raise SystemExit(f"Tính thời hạn {label} không mặc định đóng đủ ba căn cứ pháp lý.")
    for prefix in ("tg", "tgiam", "start"):
        day = deadline.index(f'id="{prefix}-day"')
        month = deadline.index(f'id="{prefix}-month"')
        year = deadline.index(f'id="{prefix}-year"')
        if not day < month < year:
            raise SystemExit(f"Tính thời hạn {label} bị đảo thứ tự Ngày/Tháng/Năm ở nhóm {prefix}.")

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
launcher_html = read(STAGE, "DesktopOfflineAssets/launcher.html")
if launcher_html.count("Phát triển bởi:") != 1 or "landing-page" not in launcher_html:
    raise SystemExit("Launcher desktop phải có trang chào mừng và đúng một chữ ký.")
if 'class="dashboard-lotus-bg"' not in launcher_html or 'srcset="./static/lotus.webp"' not in launcher_html:
    raise SystemExit("Launcher desktop chưa dùng giao diện nền hoa sen của bản GitHub.")
if '<section class="tool-section tool-section-online"' in launcher_html or "github.com" in launcher_html:
    raise SystemExit("Launcher desktop còn nhóm công cụ trực tuyến hoặc liên kết phát hành.")
if "/__offline_assets/tailwind/tailwind.js" not in launcher_html or "window.pywebview.api.launch" not in launcher_html:
    raise SystemExit("Launcher desktop chưa dùng tài nguyên và API mở công cụ cục bộ.")
if launcher_html.count('@font-face{font-family:"Inter"') != 3 or launcher_html.count('@font-face{font-family:"Be Vietnam Pro"') != 3:
    raise SystemExit("Launcher desktop chưa ánh xạ đủ font cục bộ cho trang chào mừng và dashboard.")
if "/__offline_assets/brand/brand.css" in launcher_html:
    raise SystemExit("Launcher desktop không được nạp CSS nhận diện của công cụ con.")
if 'launcher.html").read_text' not in launcher or 'launcher_assets' not in launcher:
    raise SystemExit("Ứng dụng desktop chưa nạp launcher đã staging.")
dashboard = read(ROOT, "index.html")
if dashboard.count("Phát triển bởi:") != 1 or 'class="footer-logo"' not in dashboard:
    raise SystemExit("Bảng điều hành gốc phải có đúng một chữ ký và logo footer riêng.")
if "display: flex; align-items: center; justify-content: center" not in dashboard or "white-space: nowrap" not in dashboard:
    raise SystemExit("Chữ ký bảng điều hành gốc chưa khóa chữ và logo trên cùng một dòng.")
if 'class="dashboard-lotus-bg"' not in dashboard or 'srcset="./static/lotus.webp"' not in dashboard or 'src="./static/lotus.png"' not in dashboard or "#dashboard-page::before" not in dashboard:
    raise SystemExit("Bảng điều hành gốc chưa dùng nền hoa sen không cắt ở chân trang.")
anonymizer_download = read(ROOT, "Tool/AnDanh/index.html")
if "TẢI XUỐNG CÔNG CỤ" not in anonymizer_download or "KHỞI CHẠY CÔNG CỤ" in anonymizer_download:
    raise SystemExit("Trang tải công cụ che thông tin chưa hiển thị đúng hành động tải xuống.")
renamer = read(STAGE, "Tool/FileRenamer/file_renamer_gui.py")
if "window.pywebview.api.choose_folder" not in renamer:
    raise SystemExit("Bản desktop đổi tên file chưa dùng hộp thoại chọn thư mục native.")

print("OK UI behavior: panel phụ đóng, tool con không có chữ ký, launcher có đúng một chữ ký và thông báo riêng")
