"""
convert_doc_to_md.py — Chuyển đổi file .doc, .docx sang Markdown
=================================================================
- Quét đệ quy thư mục, giữ nguyên file gốc
- Tạo file .md bên cạnh file gốc
- .docx: dùng python-docx (thuần Python, không cần Word)
- .doc:  dùng win32com (Word COM Automation) → lưu tạm .docx → python-docx
- File không có text → skip + log [NO_TEXT]

Usage:
    python convert_doc_to_md.py                           # Mặc định quét Kho_tai_lieu_da_phan_loai
    python convert_doc_to_md.py --dir <path>              # Thư mục khác
    python convert_doc_to_md.py --dry-run                 # Chỉ liệt kê, không convert
    python convert_doc_to_md.py --force                   # Ghi đè file .md đã tồn tại
    python convert_doc_to_md.py --verbose                 # Log chi tiết
    python convert_doc_to_md.py --skip-doc                # Bỏ qua file .doc, chỉ xử lý .docx
"""

import os, sys, re, argparse, time, tempfile, logging, shutil
from pathlib import Path
from typing import List, Tuple, Optional

# ============================================================
# CONFIG
# ============================================================
DEFAULT_DIR = r"deepseek_workspace\Kho_tai_lieu_da_phan_loai"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("Doc2MD")


# ============================================================
# ĐỌC FILE .docx BẰNG python-docx
# ============================================================
def read_docx_text(file_path: str) -> Optional[str]:
    """
    Trích xuất toàn bộ text từ file .docx.
    Returns:
        str nếu có text, None nếu không có text.
    """
    try:
        from docx import Document
    except ImportError:
        logger.error("Thiếu python-docx. Cài đặt: pip install python-docx")
        sys.exit(1)

    try:
        # Dùng str(Path) để chuẩn hóa đường dẫn Unicode
        doc = Document(str(Path(file_path)))
    except Exception as e:
        logger.debug(f"  Lỗi mở .docx: {e}")
        return None

    text_lines = []

    # Paragraphs
    for para in doc.paragraphs:
        t = para.text.strip()
        if t:
            text_lines.append(t)

    # Tables
    for table_idx, table in enumerate(doc.tables, 1):
        text_lines.append(f"\n### Bảng {table_idx}")
        for row_idx, row in enumerate(table.rows):
            row_data = []
            for cell in row.cells:
                row_data.append(cell.text.strip())
            text_lines.append(" | ".join(row_data))

    if not text_lines:
        return None

    return "\n\n".join(text_lines)


# ============================================================
# HELPER: LẤY SHORT PATH (8.3) ĐỂ TRÁNH LỖI UNICODE VỚI COM
# ============================================================
def _get_short_path(long_path: str) -> str:
    """
    Lấy short path (8.3 format) của file/thư mục để tránh lỗi
    Unicode với Word COM Automation và các ứng dụng cũ.
    Nếu không lấy được short path thì trả về long_path gốc.
    """
    try:
        import ctypes
        from ctypes import wintypes
        buffer = ctypes.create_unicode_buffer(300)
        GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
        GetShortPathNameW.restype = wintypes.DWORD
        GetShortPathNameW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, wintypes.DWORD]
        result = GetShortPathNameW(str(Path(long_path)), buffer, 300)
        if result > 0:
            return buffer.value
    except Exception:
        pass
    return long_path


# ============================================================
# ĐỌC FILE .doc BẰNG WORD COM → TẠM .docx → python-docx
# ============================================================
def read_doc_via_win32com(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Mở file .doc bằng Microsoft Word (COM), lưu tạm thành .docx,
    rồi đọc bằng python-docx. Xóa file tạm sau khi xong.

    Returns:
        (text_or_None, error_message_or_None)
    """
    import pythoncom
    import win32com.client

    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        return None, "File không tồn tại"

    # Lấy short path để tránh lỗi Unicode với Word COM Automation
    short_path = _get_short_path(abs_path)

    word = None
    doc = None
    temp_docx = None

    try:
        pythoncom.CoInitialize()
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False

        # Mở file .doc — dùng short path cho COM
        doc = word.Documents.Open(short_path, ReadOnly=True)

        # Lưu tạm thành .docx
        temp_fd, temp_docx = tempfile.mkstemp(suffix=".docx", prefix="temp_doc_")
        os.close(temp_fd)

        doc.SaveAs2(temp_docx, FileFormat=16)  # 16 = wdFormatDocumentDefault (.docx)
        doc.Close(SaveChanges=False)
        doc = None

        # Đọc text từ file .docx tạm
        text = read_docx_text(temp_docx)
        return text, None

    except Exception as e:
        return None, str(e)

    finally:
        # Dọn dẹp
        try:
            if doc is not None:
                doc.Close(SaveChanges=False)
        except:
            pass
        try:
            if word is not None:
                word.Quit()
        except:
            pass
        try:
            pythoncom.CoUninitialize()
        except:
            pass
        # Xóa file tạm
        if temp_docx and os.path.exists(temp_docx):
            try:
                os.remove(temp_docx)
            except:
                pass


# ============================================================
# QUÉT THƯ MỤC ĐỆ QUY, TÌM FILE CẦN CONVERT
# ============================================================
def scan_directory(root_dir: str, force: bool = False, skip_doc: bool = False) -> List[Tuple[str, str, str]]:
    """
    Quét đệ quy thư mục, tìm file .docx và .doc chưa có .md tương ứng.

    Args:
        root_dir: Thư mục gốc
        force: True = bao gồm cả file đã có .md
        skip_doc: True = bỏ qua file .doc

    Returns:
        List of (extension, source_path, md_path)
    """
    if not os.path.isdir(root_dir):
        logger.error(f"Thư mục không tồn tại: {root_dir}")
        return []

    extensions = [".docx"]
    if not skip_doc:
        extensions.append(".doc")

    files_to_convert = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext not in extensions:
                continue

            source_path = os.path.join(dirpath, filename)
            stem = Path(filename).stem
            md_path = os.path.join(dirpath, stem + ".md")

            if not force and os.path.exists(md_path):
                continue  # Đã có .md → skip

            files_to_convert.append((ext, source_path, md_path))

    return files_to_convert


# ============================================================
# CHUYỂN ĐỔI 1 FILE
# ============================================================
def convert_one(ext: str, source_path: str, md_path: str, dry_run: bool = False) -> str:
    """
    Chuyển đổi 1 file sang .md.

    Returns:
        Trạng thái: "ok", "skip", "notext", "error"
    """
    filename = os.path.basename(source_path)

    if dry_run:
        logger.info(f"  [DRY-RUN] {filename} -> {Path(md_path).name}")
        return "dry-run"

    if ext == ".docx":
        text = read_docx_text(source_path)
        if text is None:
            logger.warning(f"  [NO_TEXT] {filename} - Không có nội dung text, bỏ qua")
            return "notext"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"  [OK] {filename} -> {Path(md_path).name} ({len(text)} chars)")
        return "ok"

    elif ext == ".doc":
        text, error = read_doc_via_win32com(source_path)
        if error:
            logger.error(f"  [ERROR] {filename} - {error}")
            return "error"

        if text is None:
            logger.warning(f"  [NO_TEXT] {filename} - Không có nội dung text, bỏ qua")
            return "notext"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"  [OK] {filename} -> {Path(md_path).name} ({len(text)} chars)")
        return "ok"

    return "error"


# ============================================================
# XỬ LÝ TOÀN BỘ THƯ MỤC
# ============================================================
def process_directory(
    root_dir: str,
    force: bool = False,
    dry_run: bool = False,
    skip_doc: bool = False,
) -> dict:
    """
    Quét và chuyển đổi toàn bộ file .doc/.docx trong thư mục.

    Returns:
        dict thống kê: {total, ok, skip_existing, notext, error, dry_run}
    """
    files = scan_directory(root_dir, force=force, skip_doc=skip_doc)

    if not files:
        logger.info("Không tìm thấy file nào cần chuyển đổi.")
        return {"total": 0, "ok": 0, "skip_existing": 0, "notext": 0, "error": 0, "dry_run": 0}

    # Đếm file đã có .md để biết skip_existing
    total_all = sum(1 for _, _, md in files if not os.path.exists(md))
    skip_existing = 0
    # Đếm lại sau khi quét đầy đủ để biết skip_existing
    all_exts = [".docx"] if skip_doc else [".docx", ".doc"]
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            ext = Path(fn).suffix.lower()
            if ext not in all_exts:
                continue
            stem = Path(fn).stem
            md_path = os.path.join(dirpath, stem + ".md")
            if os.path.exists(md_path) and not force:
                skip_existing += 1

    stats = {"total": len(files), "ok": 0, "skip_existing": skip_existing,
             "notext": 0, "error": 0, "dry_run": 0}

    logger.info(f"\n{'='*60}")
    logger.info(f"THƯ MỤC: {root_dir}")
    logger.info(f"Tổng file cần xử lý: {len(files)}  |  Đã có .md (skip): {skip_existing}")
    logger.info(f"Dry-run: {dry_run}  |  Force: {force}  |  Skip .doc: {skip_doc}")
    logger.info(f"{'='*60}\n")

    start_time = time.time()

    for idx, (ext, src, md) in enumerate(files, 1):
        filename = os.path.basename(src)
        logger.info(f"[{idx}/{len(files)}] {filename} ({ext})")

        result = convert_one(ext, src, md, dry_run=dry_run)
        stats[result] = stats.get(result, 0) + 1

        # Delay nhẹ giữa các file để Word không bị quá tải
        if ext == ".doc" and not dry_run and idx < len(files):
            time.sleep(0.5)

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)

    # Tổng kết
    logger.info(f"\n{'='*60}")
    logger.info(f"KẾT QUẢ")
    logger.info(f"{'='*60}")
    logger.info(f"  Tổng số:       {stats['total']}")
    logger.info(f"  OK:            {stats['ok']}")
    logger.info(f"  Đã có .md:     {stats['skip_existing']}")
    logger.info(f"  No text:       {stats['notext']}")
    logger.info(f"  Lỗi:           {stats['error']}")
    if dry_run:
        logger.info(f"  Dry-run:       {stats['dry_run']}")
    logger.info(f"  Thời gian:     {minutes}m {seconds}s")
    logger.info(f"{'='*60}")

    return stats


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Chuyển đổi .doc/.docx sang Markdown (giữ file gốc, tạo .md bên cạnh)"
    )
    parser.add_argument(
        "--dir", "-d", type=str, default=DEFAULT_DIR,
        help=f"Thư mục gốc (mặc định: {DEFAULT_DIR})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Chỉ liệt kê file sẽ xử lý, không convert thật"
    )
    parser.add_argument(
        "--force", "-f", action="store_true",
        help="Ghi đè file .md nếu đã tồn tại"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Log chi tiết (DEBUG level)"
    )
    parser.add_argument(
        "--skip-doc", action="store_true",
        help="Bỏ qua file .doc, chỉ xử lý .docx"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Kiểm tra thư mục
    root = args.dir
    if not os.path.isabs(root):
        # Tương đối → tuyệt đối từ cwd
        root = os.path.abspath(root)

    if not os.path.isdir(root):
        logger.error(f"Thư mục không tồn tại: {root}")
        sys.exit(1)

    logger.info(f"Bắt đầu quét: {root}")
    logger.info(f"Dry-run: {args.dry_run} | Force: {args.force} | Skip .doc: {args.skip_doc}")

    process_directory(
        root_dir=root,
        force=args.force,
        dry_run=args.dry_run,
        skip_doc=args.skip_doc,
    )


if __name__ == "__main__":
    main()