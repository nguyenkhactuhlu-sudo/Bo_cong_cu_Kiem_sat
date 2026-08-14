"""Kiểm tra các luồng chọn file/thư mục với đường dẫn tiếng Việt có dấu."""

from __future__ import annotations

import io
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from docx import Document

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parents[1]
STAGE = Path(__file__).resolve().parent / "stage" / "payload"
sys.path.insert(0, str(Path(__file__).resolve().parent))

import main as desktop


desktop.resource_root = lambda: STAGE


def load(relative: str):
    return desktop.load_source_module(STAGE / relative)


def make_docx(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    doc.add_paragraph("Viện kiểm xát nhân dân ban hành  quyết định khởi tố.")
    doc.save(path)


with tempfile.TemporaryDirectory(prefix="kiểm_thử_đường_dẫn_") as temporary:
    base = Path(temporary) / "Hồ sơ kiểm sát số 01"
    base.mkdir()

    # Đổi tên file: thao tác trực tiếp trên thư mục và file Unicode.
    renamer_module = load("Tool/FileRenamer/file_renamer_gui.py")
    rename_dir = base / "Tài liệu cần đổi tên"
    rename_dir.mkdir()
    rename_source = rename_dir / "Báo cáo tổng kết năm 2026!!.docx"
    rename_source.write_bytes(b"unicode path")
    scan = renamer_module.app.test_client().post("/api/scan", json={"path": str(rename_dir)})
    assert scan.status_code == 200, scan.data
    scan_data = scan.get_json()
    assert scan_data["results"] and "Báo cáo" in scan_data["results"][0]["old_name"]
    execute = renamer_module.app.test_client().post(
        "/api/execute",
        json={"path": str(rename_dir), "indices": [0], "custom_names": {"0": "Hồ sơ đã chuẩn hóa.docx"}},
    )
    assert execute.status_code == 200 and execute.get_json()["renamed"] == 1, execute.data
    assert (rename_dir / "Hồ sơ đã chuẩn hóa.docx").exists()

    # Ẩn danh: multipart giữ tên file Unicode, backend lưu nội bộ bằng UUID.
    anonymizer = load("Tool/AnDanh/andanh_app/app.py")
    anonymizer_source = base / "Văn bản cần che thông tin.docx"
    make_docx(anonymizer_source)
    with anonymizer_source.open("rb") as stream:
        response = anonymizer.app.test_client().post(
            "/upload", data={"file": (stream, anonymizer_source.name)},
            content_type="multipart/form-data",
        )
    assert response.status_code == 200, response.data

    # Rà chính tả: xuất kết quả vẫn giữ tên tiếng Việt trong Content-Disposition/ZIP.
    spell = load("Tool/SpellChecker/app.py")
    spell_source = base / "Quyết định giải quyết vụ án.docx"
    make_docx(spell_source)
    with spell_source.open("rb") as stream:
        analyzed = spell.app.test_client().post(
            "/api/analyze", data={"file": (stream, spell_source.name)},
            content_type="multipart/form-data",
        )
    assert analyzed.status_code == 200, analyzed.data
    payload = analyzed.get_json()
    exported = spell.app.test_client().post(
        "/api/export", json={"job": payload["job"], "mode": "both", "accepted": []},
    )
    assert exported.status_code == 200
    with zipfile.ZipFile(io.BytesIO(exported.data)) as archive:
        assert all("Quyết định giải quyết vụ án" in name for name in archive.namelist())

    # OCR: kiểm tra nhận tên PDF Unicode và sinh đầu ra Unicode mà không cần chạy Tesseract.
    ocr = load("Tool/OCR_PDF_Tool/source/main.py")
    pdf_data = b"%PDF-1.4\n% Unicode filename QA\n%%EOF"
    with ocr.app.test_request_context(
        "/api/ocr", method="POST",
        data={"file": (io.BytesIO(pdf_data), "Biên bản khám nghiệm hiện trường.pdf")},
        content_type="multipart/form-data",
    ):
        uploaded = ocr.request.files["file"]
        upload_path, original_stem = ocr._uploaded_pdf(uploaded)
    assert Path(upload_path).exists() and Path(upload_path).name.isascii()
    assert original_stem == "Biên bản khám nghiệm hiện trường"
    generated = ocr.OutputGenerator(original_stem, str(base / "Kết quả OCR")).generate(["Nội dung"], "txt")
    assert Path(generated).exists() and original_stem in Path(generated).name

print("OK Unicode: chọn/đọc/ghi file và thư mục tiếng Việt có dấu ở 4 công cụ")
