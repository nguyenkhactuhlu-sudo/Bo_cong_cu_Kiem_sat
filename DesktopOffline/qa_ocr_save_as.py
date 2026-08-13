"""Kiểm thử Save As cho một kết quả OCR và ZIP hàng loạt."""

from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path

from werkzeug.serving import make_server

import main as desktop


STAGE = Path(__file__).resolve().parent / "stage" / "payload"
desktop.resource_root = lambda: STAGE
os.environ["BCKS_DESKTOP_OFFLINE"] = "1"


class FakeWindow:
    def __init__(self, targets):
        self.targets = iter(targets)
        self.calls = 0

    def create_file_dialog(self, *_args, **_kwargs):
        self.calls += 1
        return (str(next(self.targets)),)


tool = desktop.TOOLS["ocr"]
module = desktop.load_source_module(STAGE / tool["source"])
app = module.app
app.template_folder = str(STAGE / tool["template_folder"])
app.static_folder = str(STAGE / tool["static_folder"])

with tempfile.TemporaryDirectory() as temporary:
    temp = Path(temporary)
    source_a = Path(module.OUTPUT_DIR) / "qa_ocr_a.txt"
    source_b = Path(module.OUTPUT_DIR) / "qa_ocr_b.md"
    source_a.write_text("Kết quả OCR tiếng Việt", encoding="utf-8")
    source_b.write_text("# Kết quả OCR", encoding="utf-8")
    target_a = temp / "ket_qua.txt"
    target_zip = temp / "ket_qua.zip"
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        api = desktop.ToolApi(f"http://127.0.0.1:{server.server_port}")
        api.window = FakeWindow([target_a, target_zip])
        single = api.save_ocr_file(source_a.name)
        zipped = api.save_ocr_zip([source_a.name, source_b.name])
    finally:
        server.shutdown()
        thread.join(timeout=5)
        source_a.unlink(missing_ok=True)
        source_b.unlink(missing_ok=True)

    if not single.get("ok") or target_a.read_text(encoding="utf-8") != "Kết quả OCR tiếng Việt":
        raise SystemExit(f"Lưu kết quả OCR đơn thất bại: {single}")
    if not zipped.get("ok") or not target_zip.read_bytes().startswith(b"PK"):
        raise SystemExit(f"Lưu ZIP OCR thất bại: {zipped}")
    if api.window.calls != 2:
        raise SystemExit("Save As OCR không được gọi đúng hai lần.")
    print(f"OK OCR Save As: file đơn {target_a.stat().st_size} bytes, ZIP {target_zip.stat().st_size} bytes")
