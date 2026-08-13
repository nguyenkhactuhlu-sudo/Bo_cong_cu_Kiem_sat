"""Kiểm tra các link và gói ZIP được trang web phát hành."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGES = {
    "Tool/AnDanh/AnDanhTool.zip": {"AnDanhTool.exe", "HuongDanSuDung.txt"},
    "Tool/FileRenamer/FileRenamer.zip": {
        "FileRenamerPortable/FileRenamerPortable.exe",
        "FileRenamerPortable/HUONG_DAN_SU_DUNG.txt",
    },
    "Tool/SpellChecker/RaSoatChinhTa.zip": {"RaSoatChinhTa.exe", "HuongDanSuDung.txt"},
    "Tool/OCR_PDF_Tool/OCR_PDF_Tool.zip": {
        "OCR_PDF_Tool/OCR_PDF_Tool.exe",
        "OCR_PDF_Tool/HuongDanSuDung.txt",
        "OCR_PDF_Tool/Tesseract-OCR/tesseract.exe",
        "OCR_PDF_Tool/Tesseract-OCR/tessdata/vie.traineddata",
    },
}

for relative, required in PACKAGES.items():
    path = ROOT / relative
    if not path.exists() or path.stat().st_size < 1_000_000:
        raise SystemExit(f"Thiếu hoặc hỏng gói phát hành: {relative}")
    with zipfile.ZipFile(path) as archive:
        broken = archive.testzip()
        if broken:
            raise SystemExit(f"ZIP lỗi CRC {relative}: {broken}")
        names = {name.replace("\\", "/") for name in archive.namelist()}
        missing = required - names
        if missing:
            raise SystemExit(f"{relative} thiếu: {', '.join(sorted(missing))}")

pages = {
    "Tool/AnDanh/index.html": "Tool/AnDanh/AnDanhTool.zip",
    "Tool/FileRenamer/index.html": "Tool/FileRenamer/FileRenamer.zip",
    "Tool/SpellChecker/index.html": "Tool/SpellChecker/RaSoatChinhTa.zip",
    "Tool/OCR_PDF_Tool/index.html": "Tool/OCR_PDF_Tool/OCR_PDF_Tool.zip",
}
for page, package in pages.items():
    html = (ROOT / page).read_text(encoding="utf-8")
    if package not in html:
        raise SystemExit(f"Link trong {page} không trỏ đúng {package}")

stale_names = {
    "Tool/FileRenamer/index.html": ("FileRenamerGUI.exe", "FileRenamer.exe"),
    "Tool/OCR_PDF_Tool/index.html": ("Chay_OCR.bat",),
}
for page, names in stale_names.items():
    html = (ROOT / page).read_text(encoding="utf-8")
    for name in names:
        if name in html:
            raise SystemExit(f"Hướng dẫn cũ trong {page}: {name}")

dashboard = (ROOT / "index.html").read_text(encoding="utf-8")
installer_url = (
    "https://github.com/nguyenkhactuhlu-sudo/Bo_cong_cu_Kiem_sat/"
    "releases/latest/download/BoCongCuKiemSat_Offline_Setup.exe"
)
if installer_url not in dashboard:
    raise SystemExit("Dashboard chưa trỏ thẳng tới bộ cài Offline mới nhất.")
if "url('static/lotus.png')" not in dashboard or "#landing-page" not in dashboard:
    raise SystemExit("Trang chào chưa dùng nền lotus.png.")

print("OK: 4 ZIP hop le; link tai tool va bo cai Offline dung")
