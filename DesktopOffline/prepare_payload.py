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


def prepare_launcher() -> None:
    """Tạo launcher offline từ giao diện cổng công cụ đang phát hành trên GitHub."""
    source = (ROOT / "index.html").read_text(encoding="utf-8")
    source = source.replace(
        '<script src="https://cdn.tailwindcss.com"></script>',
        '<script src="/__offline_assets/tailwind/tailwind.js"></script>',
    )
    source = source.replace(
        "<title>Bộ Công Cụ Nghiệp Vụ - VKSND</title>",
        "<title>Bộ Công Cụ Nghiệp Vụ Offline - VKSND</title>",
    )
    local_fonts = """<style>
@font-face{font-family:"Inter";src:url("/__offline_assets/brand/fonts/BeVietnamPro-Regular.ttf") format("truetype");font-weight:300 500;font-display:block}
@font-face{font-family:"Inter";src:url("/__offline_assets/brand/fonts/BeVietnamPro-SemiBold.ttf") format("truetype");font-weight:600;font-display:block}
@font-face{font-family:"Inter";src:url("/__offline_assets/brand/fonts/BeVietnamPro-Bold.ttf") format("truetype");font-weight:700 900;font-display:block}
@font-face{font-family:"Be Vietnam Pro";src:url("/__offline_assets/brand/fonts/BeVietnamPro-Regular.ttf") format("truetype");font-weight:300 500;font-display:block}
@font-face{font-family:"Be Vietnam Pro";src:url("/__offline_assets/brand/fonts/BeVietnamPro-SemiBold.ttf") format("truetype");font-weight:600;font-display:block}
@font-face{font-family:"Be Vietnam Pro";src:url("/__offline_assets/brand/fonts/BeVietnamPro-Bold.ttf") format("truetype");font-weight:700 900;font-display:block}
</style>"""
    source = source.replace("</head>", local_fonts + "\n</head>", 1)

    # Bản desktop chỉ quản lý các công cụ đã được đóng gói. Không hiển thị nút
    # tải setup hoặc nhóm dịch vụ trực tuyến của website.
    source, download_count = re.subn(
        r'<a class="offline-download".*?</a>',
        '<span class="offline-download" title="Ứng dụng đang chạy hoàn toàn ngoại tuyến">'
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">'
        '<path d="M12 3l7 3v5c0 4.6-2.8 8.3-7 10-4.2-1.7-7-5.4-7-10V6l7-3z"/>'
        '<path d="M9 12l2 2 4-4" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        'Bản Offline · Xử lý trên máy</span>',
        source,
        count=1,
        flags=re.DOTALL,
    )
    source, online_section_count = re.subn(
        r'\s*<section class="tool-section tool-section-online".*?</section>',
        "",
        source,
        count=1,
        flags=re.DOTALL,
    )

    offline_tools = """var TOOLS = [
            { id:'interest', group:'offline', span:'span-4', badge:'NGOẠI TUYẾN', badgeClass:'badge-emerald', title:'Tự động tính tiền lãi', desc:'Tự động tính tiền lãi trong hạn, lãi quá hạn, lãi chậm trả trong giao dịch dân sự.', illust:ILLUST.interest, accent:'', footer:'' },
            { id:'court_fee', group:'offline', span:'span-4', badge:'NGOẠI TUYẾN', badgeClass:'badge-emerald', title:'Tính án phí', desc:'Tra cứu và tự động tính nhanh số tiền án phí hình sự và dân sự.', illust:ILLUST.courtScale, accent:'', footer:'' },
            { id:'deadline', group:'offline', span:'span-4', badge:'NGOẠI TUYẾN', badgeClass:'badge-emerald', title:'Tính tuổi — Tính thời hạn', desc:'Tính tuổi, ngày tháng năm và kiểm soát thời hạn tạm giữ, tạm giam, tố tụng.', illust:ILLUST.deadline, accent:'', footer:'' },
            { id:'anonymizer', group:'offline', span:'span-7', badge:'NGOẠI TUYẾN', badgeClass:'badge-emerald', title:'Tự động che thông tin', desc:'Tự động ẩn thông tin cá nhân trong văn bản trước khi công bố hoặc giao cho AI xử lý.', illust:ILLUST.anonymize, accent:'', footer:'' },
            { id:'renamer', group:'offline', span:'span-5', badge:'NGOẠI TUYẾN', badgeClass:'badge-emerald', title:'Tự động đổi tên file', desc:'Chuẩn hóa và đổi tên file hàng loạt, hỗ trợ đánh số bút lục hoặc tài liệu.', illust:ILLUST.rename, accent:'', footer:'' },
            { id:'spell_checker', group:'offline', span:'span-5', badge:'NGOẠI TUYẾN', badgeClass:'badge-emerald', title:'Rà soát chính tả văn bản Word', desc:'Phát hiện lỗi chính tả, cụm từ nghiệp vụ, khoảng trắng và dấu câu trong văn bản Word.', illust:ILLUST.spellCheck, accent:'', footer:'<span>Không AI · Không gửi dữ liệu lên mạng</span>' },
            { id:'ocr', group:'offline', span:'span-7', badge:'NGOẠI TUYẾN', badgeClass:'badge-emerald', title:'Nhận dạng chữ trong file PDF, file ảnh', desc:'Trích xuất chữ từ PDF và ảnh, cho phép xuất Word, Markdown hoặc TXT.', illust:ILLUST.ocrScan, accent:'', footer:'' }
        ];"""
    source, tools_count = re.subn(
        r"var TOOLS = \[.*?\n        \];",
        offline_tools,
        source,
        count=1,
        flags=re.DOTALL,
    )

    render_function = """function renderToolCards(){
            var offlineHtml='';
            for(var i=0;i<TOOLS.length;i++){
                var t=TOOLS[i];
                var card='<button type="button" class="bento-card '+t.span+' '+t.accent+'" data-tool-id="'+t.id+'" onclick="openTool(\\''+t.id+'\\')">';
                card+='<div><div class="bento-card-top"><div><span class="bento-card-badge '+t.badgeClass+'">'+t.badge+'</span>';
                card+='<h3 class="bento-card-title">'+t.title+'</h3></div><div class="bento-illust">'+t.illust+'</div></div>';
                card+='<p class="bento-card-desc">'+t.desc+'</p></div>';
                if(t.footer) card+='<div class="bento-card-footer">'+t.footer+'</div>';
                offlineHtml+=card+'</button>';
            }
            offlineToolsGrid.innerHTML=offlineHtml;
            offlineToolsCount.textContent=TOOLS.length+' công cụ';
        }"""
    source, render_count = re.subn(
        r"function renderToolCards\(\)\{.*?\n        \}",
        lambda _match: render_function,
        source,
        count=1,
        flags=re.DOTALL,
    )

    open_function = """function openTool(toolId){
            var tool=null;
            for(var i=0;i<TOOLS.length;i++){ if(TOOLS[i].id===toolId){ tool=TOOLS[i]; break; } }
            if(!tool) return;
            if(!(window.pywebview && window.pywebview.api)){
                alert('Không thể kết nối với bộ khởi chạy Offline.');
                return;
            }
            window.pywebview.api.launch(toolId).then(function(result){
                if(!result.ok) alert(result.message || 'Không thể mở công cụ.');
            }).catch(function(error){ alert('Không thể mở công cụ: '+error); });
        }"""
    source, open_count = re.subn(
        r"function openTool\(toolId\)\{.*?\n        \}",
        lambda _match: open_function,
        source,
        count=1,
        flags=re.DOTALL,
    )

    if (download_count, online_section_count, tools_count, render_count, open_count) != (1, 1, 1, 1, 1):
        raise SystemExit("Không thể đồng bộ giao diện launcher offline từ index.html.")

    target = STAGE / "DesktopOfflineAssets" / "launcher.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8", newline="\n")


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
        is_launcher = path.name == "launcher.html" and path.parent.name == "DesktopOfflineAssets"
        if "</head>" in updated and BRAND_STYLESHEET not in updated and not is_launcher:
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
        vendor / "tailwind" / "tailwind.js",
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
    for folder in ("bootstrap", "fontawesome", "bootstrap-icons", "tailwind"):
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
    copy_vendor()
    prepare_launcher()
    localize_html()
    audit_no_remote_assets()
    print(f"Payload sẵn sàng: {STAGE}")
