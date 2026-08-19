"""Sao chép tài nguyên cần thiết vào staging và loại bỏ mọi CDN.

Tuyệt đối không ghi vào Tool/, Data/ hoặc index.html của dự án gốc.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGE = Path(__file__).resolve().parent / "stage" / "payload"
DESKTOP_ROOT = Path(__file__).resolve().parent
BRAND_STYLESHEET = '<link rel="stylesheet" href="/__offline_assets/brand/brand.css">'

SOURCES = [
    "static",
    "Tool/App_tinh_lai_suat",
    "Tool/App_DS",
    "Tool/AnDanh/andanh_app",
    "Tool/FileRenamer",
    "Tool/auto_install.py",
    "Tool/SpellChecker",
    "Tool/OCR_PDF_Tool/source",
    "Data/TinhTuoiThoiHan.html",
]


def copy_sources() -> None:
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    for relative in SOURCES:
        source = ROOT / relative
        target = STAGE / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(
                source, target,
                ignore=shutil.ignore_patterns("build", "dist", "__pycache__", "tests", "*.zip", "*.exe"),
            )
        else:
            shutil.copy2(source, target)
    _remove_download_pages()


def _remove_download_pages() -> None:
    """Loại các trang tải xuống web (chứa link .zip trên GitHub) khỏi payload.

    Những file index.html này là trang tải bản portable cho web portal, không
    được bản desktop offline sử dụng (tool_registry nạp file_renamer_gui.py /
    app.py). Giữ chúng sẽ làm audit_no_remote_assets() fail vì còn link mạng.
    """
    download_pages = [
        STAGE / "Tool" / "FileRenamer" / "index.html",
        STAGE / "Tool" / "SpellChecker" / "index.html",
    ]
    for path in download_pages:
        if path.exists():
            path.unlink()


def localize_html() -> None:
    replacements = {
        r'<link[^>]+fonts\.googleapis\.com[^>]*>': "",
        r'<link[^>]+fonts\.gstatic\.com[^>]*>': "",
        r'<link[^>]+cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[^>]*>':
            '<link rel="stylesheet" href="/__offline_assets/fontawesome/css/all.min.css">',
        r'<link[^>]+cdn\.jsdelivr\.net/npm/bootstrap@[^>]+bootstrap\.min\.css[^>]*>':
            '<link rel="stylesheet" href="/__offline_assets/bootstrap/bootstrap.min.css">',
        r'<link[^>]+cdn\.jsdelivr\.net/npm/bootstrap-icons@[^>]+bootstrap-icons\.css[^>]*>':
            '<link rel="stylesheet" href="/__offline_assets/bootstrap-icons/bootstrap-icons.min.css">',
        r'<script[^>]+cdn\.jsdelivr\.net/npm/bootstrap@[^>]+bootstrap\.bundle\.min\.js[^>]*></script>':
            '<script src="/__offline_assets/bootstrap/bootstrap.bundle.min.js"></script>',
    }
    for path in list(STAGE.rglob("*.html")) + list(STAGE.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        updated = text
        for pattern, replacement in replacements.items():
            updated = re.sub(pattern, replacement, updated, flags=re.IGNORECASE)
        updated = re.sub(
            r'''(?:\.\./)*static/logo_moi\.png|/static/logo_moi\.png|\{\{\s*url_for\(['"]static['"],\s*filename=['"]logo_moi\.png['"]\)\s*\}\}''',
            "/__offline_assets/brand/logo_moi.png", updated, flags=re.IGNORECASE,
        )
        if "</head>" in updated and BRAND_STYLESHEET not in updated:
            updated = updated.replace("</head>", BRAND_STYLESHEET + "</head>", 1)
        # Công cụ ẩn danh: template đã tự phát hiện môi trường desktop (pywebview)
        # và gọi window.pywebview.api.save_anonymized để hiện Save As của Windows,
        # nên không cần patch tại thời điểm đóng gói nữa.
        if path.as_posix().endswith("Tool/OCR_PDF_Tool/source/templates/index.html"):
            updated = updated.replace(
                '<a id="downloadLink" href="#" download class="btn btn-success btn-sm fw-bold">',
                '<button type="button" id="downloadLink" class="btn btn-success btn-sm fw-bold">',
            ).replace('</a>\n            </div>\n        </div>\n        <div id="singleResultContent"', '</button>\n            </div>\n        </div>\n        <div id="singleResultContent"', 1)
            updated = updated.replace(
                "dl.href = `/api/download/${data.output_file}`;",
                "dl.dataset.filename = data.output_file; dl.onclick = () => saveOcrFile(data.output_file);",
            )
            updated = re.sub(
                r'<a href="/api/download/\$\{encodeURIComponent\(r\.output_file\)\}"\s+download class="btn btn-sm btn-success" onclick="event\.stopPropagation\(\)">(.*?)</a>',
                r'<button type="button" class="btn btn-sm btn-success" onclick="event.stopPropagation();saveOcrFile(\'${r.output_file}\')">\1</button>',
                updated, flags=re.DOTALL,
            )
            zip_pattern = re.compile(r'''const resp = await fetch\('/api/batch/download'.*?URL\.revokeObjectURL\(url\);''', re.DOTALL)
            updated, zip_count = zip_pattern.subn(
                "const result = await window.pywebview.api.save_ocr_zip(files); if (!result.ok) throw new Error(result.message || 'Tải thất bại');",
                updated, count=1,
            )
            helper = """async function saveOcrFile(filename) {
        const result = await window.pywebview.api.save_ocr_file(filename);
        if (!result.ok) showError(result.message || 'Không thể lưu file');
    }

    """
            updated = updated.replace("async function downloadAllZip()", helper + "async function downloadAllZip()", 1)
            if zip_count != 1 or "save_ocr_file" not in updated:
                raise SystemExit("Không thể tích hợp Save As cho OCR.")
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")


def copy_vendor() -> None:
    vendor = Path(__file__).resolve().parent / "vendor"
    required = [
        vendor / "bootstrap" / "bootstrap.min.css",
        vendor / "bootstrap" / "bootstrap.bundle.min.js",
        vendor / "fontawesome" / "css" / "all.min.css",
        vendor / "bootstrap-icons" / "bootstrap-icons.min.css",
        vendor / "brand" / "fonts" / "BeVietnamPro-Regular.ttf",
        vendor / "brand" / "fonts" / "BeVietnamPro-SemiBold.ttf",
        vendor / "brand" / "fonts" / "BeVietnamPro-Bold.ttf",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("Thiếu tài nguyên offline:\n- " + "\n- ".join(missing))
    assets = STAGE / "DesktopOfflineAssets"
    assets.mkdir(parents=True, exist_ok=True)
    # Chỉ chép tài nguyên giao diện. WebView2 là runtime cài cạnh file EXE,
    # không được nhét thêm vào payload PyInstaller vì sẽ làm tăng gấp đôi dung lượng.
    for folder in ("bootstrap", "fontawesome", "bootstrap-icons"):
        shutil.copytree(vendor / folder, assets / folder)
    brand = assets / "brand"
    brand.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "static" / "logo_moi.png", brand / "logo_moi.png")
    shutil.copy2(DESKTOP_ROOT / "brand.css", brand / "brand.css")
    shutil.copytree(vendor / "brand" / "fonts", brand / "fonts")


def audit_no_remote_assets() -> None:
    violations = []
    for path in list(STAGE.rglob("*.html")) + list(STAGE.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), 1):
            if re.search(r"(?:src|href)\s*=\s*['\"]https?://", line, re.IGNORECASE):
                violations.append(f"{path.relative_to(STAGE)}:{line_number}")
    if violations:
        raise SystemExit("Payload còn tài nguyên mạng:\n- " + "\n- ".join(violations))


if __name__ == "__main__":
    copy_sources()
    localize_html()
    copy_vendor()
    audit_no_remote_assets()
    print(f"Payload sẵn sàng: {STAGE}")
