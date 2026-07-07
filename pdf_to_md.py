"""
PdfToMd - Chuyển đổi PDF/Ảnh sang Markdown bằng Gemini API (Standalone)
========================================================================
Features:
1. Batch/Concurrent processing: async OCR with asyncio + aiohttp
2. Anti-hallucination: prompt instruction + post-clean safety net  
3. Harmonization pass: optional 2nd pass to standardize markdown
4. Auto split PDF lớn (>30 trang)
5. Progressive delay + retry with backoff

Usage CLI:
    python pdf_to_md.py --file "duong_dan/file.pdf"
    python pdf_to_md.py --dir  "duong_dan/thu_muc/"
    python pdf_to_md.py --dir  "duong_dan/thu_muc/" --workers 3 --harmonize

Usage as module:
    from pdf_to_md import convert_file, process_directory
    ok, out_path = convert_file("path/to/file.pdf")
"""

import os, sys, re, base64, json, time, random, argparse, logging, shutil, tempfile
import asyncio
from pathlib import Path
from typing import Optional, List, Tuple
from difflib import SequenceMatcher

# ============================================================
# CONFIG (inline - không phụ thuộc file config.py)
# ============================================================
GEMINI_API_KEY = ""
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
API_DELAY_SECONDS = 3.0
MAX_RETRIES = 5
MAX_BACKOFF_SECONDS = 60.0
FAILED_DIR_NAME = "Tai_lieu_con_lai"
MAX_FILE_SIZE_MB = 10
MAX_PAGES_PER_CHUNK = 30
MIN_PYPDF_TEXT_LENGTH = 50
DEFAULT_WORKERS = 3
FUZZY_THRESHOLD = 0.85
MAX_RETRIES_PER_PAGE = 3
MAX_GEMINI_MB = 20
SUPPORTED_EXTENSIONS = {".pdf":"PDF", ".jpg":"JPEG", ".jpeg":"JPEG", ".png":"PNG",
    ".tiff":"TIFF", ".tif":"TIFF", ".bmp":"BMP", ".gif":"GIF", ".webp":"WebP"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("PDF2MD")

# ============================================================
# API KEY LOADING
# ============================================================
def _load_gemini_key_from_file() -> str:
    """Tìm API key Gemini từ file API keys.txt trong cùng thư mục script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    keys_file = os.path.join(script_dir, "API keys.txt")
    if not os.path.exists(keys_file):
        return ""
    try:
        with open(keys_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("|")
                if len(parts) >= 2:
                    provider = parts[0].strip().lower()
                    key = parts[1].strip()
                    if provider == "gemini" and key:
                        return key
        return ""
    except Exception:
        return ""

def get_api_key() -> str:
    k = (GEMINI_API_KEY or "").strip()
    if k: return k
    k = _load_gemini_key_from_file()
    if k: return k
    logger.error("KHONG TIM THAY GEMINI API KEY!"); sys.exit(1)

# ============================================================
# PYPDF TEXT EXTRACTION (free fallback)
# ============================================================
def _is_valid_vietnamese_text(text: str) -> bool:
    if not text or len(text.strip()) < MIN_PYPDF_TEXT_LENGTH:
        return False
    valid_pattern = re.compile(
        r'[a-zA-Z0-9'
        r'\u00C0-\u00C3\u00C8\u00C9\u00CA\u00CC\u00CD\u00D2-\u00D5\u00D9\u00DA\u00DD'
        r'\u00E0-\u00E3\u00E8\u00E9\u00EA\u00EC\u00ED\u00F2-\u00F5\u00F9\u00FA\u00FD'
        r'\u0102\u0103\u0110\u0111\u01A0\u01A1\u01AF\u01B0'
        r'\u1EA0-\u1EF9'
        r'\s.,;:!?()\[\]{}\-–—"\'/%\n\r\t'
        r'0-9'
        r']+',
        re.UNICODE
    )
    valid_chars = len(valid_pattern.findall(text))
    total_chars = len(text)
    ratio = valid_chars / total_chars if total_chars > 0 else 0
    return ratio >= 0.6

def _is_good_enough_for_fuzzy(text: str) -> bool:
    if not text or len(text) < 50:
        return False
    viet_chars = len(re.findall(r'[\u00C0-\u1EF9\u0110\u0111]', text, re.UNICODE))
    total_chars = len(text)
    ratio = viet_chars / total_chars if total_chars > 0 else 0
    return ratio > 0.05

def read_pdf_with_pypdf(file_path: str) -> Optional[str]:
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t and t.strip():
                parts.append(t.strip())
        if parts:
            text = "\n\n".join(parts)
            if _is_valid_vietnamese_text(text.strip()):
                return text.strip()
        return None
    except Exception as e:
        logger.debug(f"  pypdf loi: {e}")
        return None

# ============================================================
# SPLIT PDF
# ============================================================
def get_pdf_info(file_path: str) -> Tuple[int, float]:
    sz = os.path.getsize(file_path) / 1048576
    try:
        from pypdf import PdfReader
        return len(PdfReader(file_path).pages), sz
    except: return 0, sz

def split_pdf(file_path: str, mp: int = MAX_PAGES_PER_CHUNK) -> List[str]:
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(file_path)
    if len(reader.pages) <= mp: return [file_path]
    td = tempfile.mkdtemp(prefix="pdf_split_")
    cf, stem = [], Path(file_path).stem
    for s in range(0, len(reader.pages), mp):
        e = min(s + mp, len(reader.pages))
        w = PdfWriter()
        for i in range(s, e): w.add_page(reader.pages[i])
        p = os.path.join(td, f"{stem}_p{s//mp+1}.pdf")
        with open(p, "wb") as f: w.write(f)
        cf.append(p)
    return cf

# ============================================================
# FUZZY CHECK (Anti-Hallucination)
# ============================================================
def normalize_text(text: str, remove_whitespace: bool = True) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    if remove_whitespace:
        text = re.sub(r'\s+', '', text)
    else:
        text = re.sub(r'\s+', ' ', text).strip()
    return text

def fuzzy_check(original: str, gemini_output: str, threshold: float = FUZZY_THRESHOLD) -> Tuple[bool, float]:
    a = normalize_text(original)
    b = normalize_text(gemini_output)
    if not a or not b:
        return True, 1.0
    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio >= threshold, ratio

# ============================================================
# CLEAN PAGE RESULT (anti-hallucination safety net)
# ============================================================
def clean_page_result(text: str) -> str:
    """Làm sạch kết quả OCR: xóa hallucination dấu chấm, gỡ code block."""
    if not text:
        return text
    text = re.sub(r'\.{50,}', '... [nội dung bị thiếu]', text)
    text = re.sub(r'^```(?:markdown|md)?\s*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# ============================================================
# HARMONIZATION PASS
# ============================================================
HARMONIZE_PROMPT = """Ban la mot tro ly bien tap van ban tieng Viet chuyen nghiep. Hay chuan hoa doan van ban sau day:

QUY TAC:
1. Ghep cac dong bi ngat khong dung cho thanh doan van hoan chinh (khong duoc thay doi noi dung)
2. Dinh dang Markdown dung chuan: # cho tieu de, ## cho muc, ### cho tieu muc
3. Xoa cac ky tu rac OCR (ky tu la, ky tu thua, dau cach thua)
4. Giua cac doan van phai co 1 dong trong
5. GIU NGUYEN tat ca so lieu, ten rieng, thuat ngu phap ly
6. KHONG DUOC viet lai, them bot, hoac thay doi noi dung goc
7. Neu gap TextBox/Watermark/So trang -> xoa bo

Tra ve CHI NOI DUNG da chuan hoa, khong giai thich gi them."""

async def _harmonize_text_async(api_key: str, text: str, session) -> Optional[str]:
    url = f"{GEMINI_BASE_URL}/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [
            {"text": HARMONIZE_PROMPT},
            {"text": f"\n\n<van_ban>\n{text}\n</van_ban>"}
        ]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192}
    }
    for at in range(1, 3):
        try:
            async with session.post(url, json=payload, timeout=120) as r:
                if r.status == 200:
                    data = await r.json()
                    cands = data.get("candidates", [])
                    if cands:
                        parts = cands[0].get("content", {}).get("parts", [])
                        result = "".join(p.get("text","") for p in parts)
                        if result.strip():
                            ok, ratio = fuzzy_check(text, result, 0.80)
                            if ok:
                                return result.strip()
                            else:
                                logger.warning(f"  Harmonize rejected (fuzzy={ratio:.2f}), keeping original")
                                return None
                elif r.status == 429:
                    await asyncio.sleep(min(10 * (2 ** at), 60))
                elif r.status == 503:
                    await asyncio.sleep(min(5 * (2 ** at), 60))
        except Exception as e:
            logger.warning(f"  Harmonize error: {e}")
            if at < 2:
                await asyncio.sleep(3)
    return None

# ============================================================
# ASYNC OCR PER PAGE
# ============================================================
async def _ocr_page_async(api_key: str, fp: str, label: str, 
                          session, semaphore: asyncio.Semaphore,
                          original_text: str = "") -> Tuple[Optional[str], str]:
    async with semaphore:
        url = f"{GEMINI_BASE_URL}/models/{GEMINI_MODEL}:generateContent?key={api_key}"
        try:
            with open(fp, "rb") as f: d = f.read()
            if len(d) / 1048576 > MAX_GEMINI_MB:
                return None, f"File qua lon"
            b64 = base64.b64encode(d).decode()
        except Exception as e:
            return None, f"Loi doc: {e}"

        mm = {".pdf":"application/pdf", ".jpg":"image/jpeg", ".jpeg":"image/jpeg",
              ".png":"image/png", ".tiff":"image/tiff", ".tif":"image/tiff",
              ".bmp":"image/bmp", ".gif":"image/gif", ".webp":"image/webp"}
        mt = mm.get(Path(fp).suffix.lower(), "application/octet-stream")

        prompt = ("Hãy trích xuất toàn bộ nội dung văn bản từ file này và chuyển sang định dạng Markdown.\n"
                  "QUY TẮC BẮT BUỘC:\n"
                  "- Giữ nguyên cấu trúc: tiêu đề, đoạn văn, danh sách, bảng biểu.\n"
                  "- Giữ nguyên tiếng Việt có dấu. Không thêm bất kỳ bình luận hay giải thích nào.\n"
                  "- TUYỆT ĐỐI KHÔNG thêm chuỗi dấu chấm dài (.......) dưới bất kỳ hình thức nào. "
                  "Nếu nội dung trống hoặc không đọc được, để nguyên dòng trống.\n"
                  "- TUYỆT ĐỐI KHÔNG bọc nội dung trong ```markdown hoặc ``` code block.\n"
                  "- RANH GIỚI TRANG: nếu có, dùng chính xác <!-- new_page --> trên 1 dòng riêng.\n"
                  "- KHÔNG dùng --- để phân cách nội dung.")

        payload = {
            "contents": [{"parts": [
                {"inline_data": {"mime_type": mt, "data": b64}},
                {"text": prompt}
            ]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 8192}
        }

        for at in range(1, MAX_RETRIES_PER_PAGE + 1):
            try:
                async with session.post(url, json=payload, timeout=180) as r:
                    if r.status == 200:
                        data = await r.json()
                        cands = data.get("candidates", [])
                        if cands:
                            parts = cands[0].get("content", {}).get("parts", [])
                            txt = "".join(p.get("text","") for p in parts)
                            if txt.strip():
                                if original_text and _is_good_enough_for_fuzzy(original_text):
                                    is_similar, ratio = fuzzy_check(original_text, txt)
                                    if not is_similar:
                                        logger.warning(f"  {label} REJECTED (fuzzy={ratio:.2f})")
                                        return None, f"rejected (fuzzy={ratio:.2f})"
                                return txt.strip(), "ok"
                            logger.warning(f"  {label} Empty (at {at})")
                            await asyncio.sleep(min(API_DELAY_SECONDS * (2 ** at), MAX_BACKOFF_SECONDS))
                            continue
                    elif r.status == 429:
                        w = min(10 * (2 ** at), MAX_BACKOFF_SECONDS)
                        logger.warning(f"  {label} Rate limit! backoff {w}s")
                        await asyncio.sleep(w)
                    elif r.status == 503:
                        w = min(5 * (2 ** at), MAX_BACKOFF_SECONDS)
                        logger.warning(f"  {label} 503 backoff {w}s")
                        await asyncio.sleep(w)
                    elif r.status in (403, 404):
                        return None, f"API error {r.status}"
                    else:
                        logger.warning(f"  {label} HTTP {r.status} (at {at})")
            except asyncio.TimeoutError:
                logger.warning(f"  {label} Timeout (at {at})")
            except Exception as e:
                logger.warning(f"  {label} Loi: {e} (at {at})")
            
            if at < MAX_RETRIES_PER_PAGE:
                await asyncio.sleep(min(API_DELAY_SECONDS * (2 ** at), MAX_BACKOFF_SECONDS))
        
        return None, f"That bai sau {MAX_RETRIES_PER_PAGE} lan"

# ============================================================
# OCR FILE (ASYNC BATCH)
# ============================================================
async def _ocr_file_async(api_key: str, file_path: str, label: str = "",
                          workers: int = DEFAULT_WORKERS,
                          harmonize: bool = False) -> Optional[str]:
    import aiohttp
    
    timeout = aiohttp.ClientTimeout(total=300, connect=30)
    semaphore = asyncio.Semaphore(workers)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            page_count = len(reader.pages)
        except:
            page_count = 1
        
        if page_count <= 1:
            txt, status = await _ocr_page_async(api_key, file_path, label, session, semaphore)
            if txt is None:
                logger.warning(f"  {label} OCR failed: {status}")
                return None
            txt = clean_page_result(txt)
        else:
            tasks = []
            for page_num in range(page_count):
                try:
                    orig = reader.pages[page_num].extract_text() or ""
                except:
                    orig = ""
                
                from pypdf import PdfWriter
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num])
                tmp_page = os.path.join(tempfile.mkdtemp(prefix="ocr_page_"), f"p{page_num+1}.pdf")
                with open(tmp_page, "wb") as f:
                    writer.write(f)
                
                page_label = f"{label} p{page_num+1}/{page_count}"
                tasks.append(_ocr_page_async(api_key, tmp_page, page_label, 
                                            session, semaphore, orig))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            txt = []
            failed = 0
            rejected = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"  {label} p{i+1} exception: {result}")
                    failed += 1
                elif result[0] is not None:
                    txt.append(clean_page_result(result[0]))
                elif "rejected" in str(result[1]):
                    rejected += 1
                    try:
                        fallback = reader.pages[i].extract_text() or ""
                        if fallback.strip():
                            txt.append(fallback)
                    except:
                        pass
                else:
                    failed += 1
            
            txt = "\n\n<!-- new_page -->\n\n".join(txt) if txt else None
            
            if failed or rejected:
                logger.info(f"  {label} OCR done: {len(txt.split(chr(10)))} lines, "
                          f"{failed} failed, {rejected} rejected")
        
        if not txt:
            return None
        
        if harmonize:
            logger.info(f"  {label} Harmonizing...")
            if len(txt) > 50000:
                chunks = [txt[i:i+50000] for i in range(0, len(txt), 50000)]
                harmonized_parts = []
                for chunk in chunks:
                    h = await _harmonize_text_async(api_key, chunk, session)
                    if h:
                        harmonized_parts.append(h)
                    else:
                        harmonized_parts.append(chunk)
                txt = "\n\n".join(harmonized_parts)
            else:
                harmonized = await _harmonize_text_async(api_key, txt, session)
                if harmonized:
                    txt = harmonized
        
        return txt.strip() if txt else None

# ============================================================
# PUBLIC API: CONVERT 1 FILE
# ============================================================
def convert_file(file_path: str, api_key: Optional[str] = None,
                 workers: int = DEFAULT_WORKERS,
                 harmonize: bool = False) -> Tuple[bool, Optional[str]]:
    """Chuyển đổi 1 file PDF/Ảnh sang Markdown.
    
    Returns:
        (success, output_path) - output_path là đường dẫn file .md đã tạo
    """
    if api_key is None: api_key = get_api_key()
    path = Path(file_path)
    if not path.exists(): return False, None

    ext = path.suffix.lower()
    out_path = str(path.parent / (path.stem + ".md"))
    if os.path.exists(out_path): return True, out_path

    logger.info(f"  Processing: {path.name} ({ext})")

    # .docx đọc trực tiếp
    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            txt = "\n\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
            if txt:
                with open(out_path, "w", encoding="utf-8") as f: f.write(txt)
                logger.info(f"  [OK] {path.name} -> .md ({len(txt)} chars)"); return True, out_path
        except: pass
        logger.warning(f"  [FAIL] {path.name} - docx loi"); return False, None

    # PDF: thử pypdf trước (miễn phí)
    if ext == ".pdf":
        pypdf_text = read_pdf_with_pypdf(file_path)
        if pypdf_text:
            with open(out_path, "w", encoding="utf-8") as f: f.write(pypdf_text)
            logger.info(f"  [OK] {path.name} -> .md (pypdf, {len(pypdf_text)} chars)")
            return True, out_path
        logger.info(f"  pypdf khong doc duoc, goi Gemini OCR...")

    # Ảnh / PDF scan -> gọi Gemini (async)
    try:
        result = asyncio.run(_ocr_file_async(api_key, file_path, path.name, 
                                             workers=workers, harmonize=harmonize))
    except RuntimeError as e:
        if "event loop" in str(e):
            import nest_asyncio
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(
                _ocr_file_async(api_key, file_path, path.name, 
                               workers=workers, harmonize=harmonize))
        else:
            raise
    
    if result:
        with open(out_path, "w", encoding="utf-8") as f: f.write(result)
        logger.info(f"  [OK] {path.name} -> .md (Gemini, {len(result)} chars)")
        return True, out_path
    else:
        logger.warning(f"  [FAIL] {path.name} - Khong doc duoc"); return False, None

# ============================================================
# PUBLIC API: XỬ LÝ THƯ MỤC
# ============================================================
def process_directory(input_dir: str, api_key: Optional[str] = None,
                      workers: int = DEFAULT_WORKERS,
                      harmonize: bool = False):
    """Quét và chuyển đổi tất cả file PDF/Ảnh trong thư mục."""
    if api_key is None: api_key = get_api_key()
    if not os.path.isdir(input_dir): 
        logger.error(f"Khong ton tai: {input_dir}"); return

    all_files = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir)
        if os.path.isfile(os.path.join(input_dir, f)) and
        (os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS or os.path.splitext(f)[1].lower() == ".docx")])

    total = len(all_files)
    logger.info(f"\n{'='*60}\nTIM THAY {total} FILE\nThu muc: {input_dir}\nWorkers: {workers}\nHarmonize: {harmonize}\n{'='*60}\n")

    ok = fail = skip = 0; failed = []

    for idx, fp in enumerate(all_files, 1):
        fn = os.path.basename(fp)
        mdp = os.path.join(input_dir, Path(fn).stem + ".md")
        if os.path.exists(mdp): skip += 1; continue

        logger.info(f"[{idx}/{total}] {fn}...")
        s, _ = convert_file(fp, api_key, workers=workers, harmonize=harmonize)
        if s: ok += 1
        else: fail += 1; failed.append(fp)

        if idx < total:
            base_delay = max(1.0, API_DELAY_SECONDS)
            delay = min(base_delay + (idx // 10) * 0.5, 10.0)
            time.sleep(delay + random.uniform(-0.2, 0.2))

    if failed:
        fd = os.path.join(input_dir, FAILED_DIR_NAME); os.makedirs(fd, exist_ok=True)
        mv = 0
        for src in failed:
            try: shutil.move(src, os.path.join(fd, os.path.basename(src))); mv += 1
            except: pass

    logger.info(f"\n{'='*60}\nKET QUA\nTong: {total} | OK: {ok} | Skip: {skip} | Fail: {fail}")
    if failed: logger.info(f"Di chuyen {mv}/{fail} file vao {FAILED_DIR_NAME}")
    logger.info(f"{'='*60}")

# ============================================================
# CLI
# ============================================================
def main():
    p = argparse.ArgumentParser(description="PdfToMd - Chuyen doi PDF/Anh sang Markdown (Standalone)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--file","-f", type=str, help="Đường dẫn file PDF/Ảnh cần chuyển đổi")
    g.add_argument("--dir","-d", type=str, help="Thư mục chứa file PDF/Ảnh cần chuyển đổi")
    p.add_argument("--verbose","-v", action="store_true", help="Hiển thị log chi tiết")
    p.add_argument("--workers","-w", type=int, default=DEFAULT_WORKERS,
                   help=f"Số request đồng thời (default: {DEFAULT_WORKERS})")
    p.add_argument("--harmonize", action="store_true",
                   help="Bật harmonization pass (chuẩn hóa Markdown + sửa lỗi OCR)")
    a = p.parse_args()
    
    if a.verbose: logging.getLogger().setLevel(logging.DEBUG)
    ak = get_api_key()
    
    if a.file:
        if not os.path.exists(a.file): 
            logger.error(f"File khong ton tai: {a.file}"); sys.exit(1)
        s, o = convert_file(a.file, ak, workers=a.workers, harmonize=a.harmonize)
        logger.info(f"\n{'[OK]' if s else '[FAIL]'} Da tao: {o}" if s else "\nThat bai")
    elif a.dir: 
        process_directory(a.dir, ak, workers=a.workers, harmonize=a.harmonize)

if __name__ == "__main__":
    main()