# OCR PDF Tool - AI/LLM Project Documentation

> **Updated:** 2026-07-13 | **Version:** 1.0.0 | **Type:** Flask Web Application  
> **Purpose:** OCR Vietnamese text from scanned PDFs → Word/Markdown/Text  
> **Stack:** Python 3.14 + Flask + Tesseract 5.4 + PyMuPDF + python-docx + Bootstrap 5

---

## 1. QUICK START (AI Agent / Developer)

```bash
# Paths
PROJECT_ROOT = d:\App_OCR_Tesseract
PYTHON_EXE   = C:\Users\Admin\AppData\Local\Python\bin\python.exe
ENTRY_POINT  = d:\App_OCR_Tesseract\OCR_App\main.py

# Run
cd d:\App_OCR_Tesseract
C:\Users\Admin\AppData\Local\Python\bin\python.exe OCR_App\main.py
# → Opens browser at http://127.0.0.1:5000

# Dependencies (already installed, DO NOT reinstall)
# PyMuPDF, Pillow, python-docx, Flask
```

---

## 2. DIRECTORY STRUCTURE

```
d:\App_OCR_Tesseract\
│
├── run.bat                           # Launcher: calls python main.py
│
├── OCR\                              # Tesseract portable (DO NOT MODIFY)
│   └── Tesseract-OCR\
│       ├── tesseract.exe             # OCR engine executable
│       ├── libtesseract-5.dll        # Core library
│       ├── *.dll                     # ~60 DLL dependencies
│       └── tessdata\
│           ├── vie.traineddata       # Vietnamese language pack
│           ├── eng.traineddata       # English language pack
│           └── osd.traineddata       # Orientation detection
│
└── OCR_App\                          # Application source
    ├── main.py                       # ★ Flask entry point + routes
    ├── config.py                     # ★ All constants, paths, settings
    ├── ocr_engine.py                 # ★ Tesseract subprocess wrapper
    ├── pdf_processor.py              # ★ PDF → PNG via PyMuPDF
    ├── output_generator.py           # ★ Generate .docx/.md/.txt output
    ├── PROJECT.md                    # 📖 This documentation
    ├── requirements.txt              # Python dependencies list
    └── build.bat                     # PyInstaller packaging script
    │
    ├── templates\
    │   └── index.html                # ★ Jinja2 template (full UI)
    │
    ├── static\
    │   └── logo_moi.png              # App logo displayed in header
    │
    ├── uploads\                      # Temp: uploaded PDF files (auto-cleaned)
    ├── temp_images\                  # Temp: rendered PNG images (auto-cleaned)
    └── outputs\                      # Final: generated output files
```

---

## 3. FILE-BY-FILE REFERENCE

### 3.1 `main.py` — Flask Application & Routes

**Purpose:** Entry point. Defines Flask app, all routes, and startup logic.

**Key variables:**
- `app = Flask(__name__, template_folder="templates", static_folder="static")`
- `app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024` (200MB max upload)

**Routes:**

| Method | Endpoint | Purpose | Input | Output |
|--------|----------|---------|-------|--------|
| GET | `/` | Serve HTML UI | — | `render_template('index.html', ...)` |
| POST | `/api/ocr` | **Single file OCR** | FormData: `file` (PDF), `language`, `format` | JSON: `{success, output_file, total_pages, pages_text[]}` |
| POST | `/api/ocr/batch` | **Batch OCR (multiple files)** | FormData: `files` (multiple PDFs), `language`, `format` | JSON: `{success, total_files, processed, errors, results[], error_list[]}` |
| GET | `/api/download/<filename>` | Download single output file | URL param: `filename` | File download |
| POST | `/api/batch/download` | Download all batch results as ZIP | JSON body: `{files: ["file1.docx", ...]}` | ZIP file download |
| GET | `/api/status` | Health check | — | JSON: `{tesseract, languages[], formats[]}` |

**Templates context** passed to `index.html`:
```python
render_template('index.html',
    title=APP_TITLE,           # "PHẦN MỀM TỰ ĐỘNG CHUYỂN ĐỔI PDF SANG WORD/MARKDOWN/TEXT"
    version=APP_VERSION,       # "1.0.0"
    tesseract_version=get_tesseract_version(),
    languages=list(OCR_LANGUAGES.keys()),
    formats=list(OUTPUT_FORMATS.keys()),
    default_lang=DEFAULT_LANGUAGE,
    default_fmt=DEFAULT_FORMAT,
)
```

**Startup flow:**
```
main() → reconfigure stdout to UTF-8 → print banner → open browser (thread) → app.run(127.0.0.1:5000)
```

**OCR processing flow** (single file, `/api/ocr`):
```
1. Receive PDF file via POST
2. Save to uploads/ with UUID prefix
3. Create OCREngine(language_code)
4. Create PDFProcessor(upload_path)
5. For each page:
   a. pdf_proc.render_page(i) → PNG file in temp_images/
   b. engine.ocr_image(png_path, output_base) → text string
   c. Delete temp PNG
6. OutputGenerator.generate(pages_text[], format) → output file in outputs/
7. Delete uploaded PDF
8. Return JSON with results
```

**Batch OCR flow** (`/api/ocr/batch`):
```
Same as single file, but:
- Receives request.files.getlist('files') → multiple files
- Processes each file sequentially in a loop
- Returns aggregated results + error_list
- Each file gets its own output in outputs/
```

---

### 3.2 `config.py` — Configuration

**Hard constants (all in one place):**

```python
# ===== PATHS =====
BASE_DIR                    # Auto-detected: dir of executable (frozen) or parent of OCR_App/
TESSERACT_DIR               # BASE_DIR/OCR/Tesseract-OCR
TESSERACT_EXE               # TESSERACT_DIR/tesseract.exe
TESSDATA_DIR                # TESSERACT_DIR/tessdata
TEMP_DIR                    # BASE_DIR/OCR_App/temp_images
UPLOAD_DIR                  # BASE_DIR/OCR_App/uploads
OUTPUT_DIR                  # BASE_DIR/OCR_App/outputs

# ===== LANGUAGES =====
OCR_LANGUAGES = {
    "Tiếng Việt": "vie",
    "Việt + Anh": "vie+eng",
}
DEFAULT_LANGUAGE = "Tiếng Việt"

# ===== OUTPUT FORMATS =====
OUTPUT_FORMATS = {
    ".docx (Word)": "docx",
    ".md (Markdown)": "md",
    ".txt (Text)": "txt",
}
DEFAULT_FORMAT = ".docx (Word)"

# ===== TESSERACT PARAMS =====
TESSERACT_PSM = 6           # Page segmentation: unified block of text
TESSERACT_OEM = 3           # OCR Engine mode: LSTM + legacy
PDF_RENDER_DPI = 300        # Render resolution
IMAGE_FORMAT = "png"

# ===== DOCX STYLING =====
DOCX_FONT_NAME = "Times New Roman"
DOCX_FONT_SIZE = 13

# ===== FLASK =====
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
APP_TITLE = "PHẦN MỀM TỰ ĐỘNG CHUYỂN ĐỔI PDF SANG WORD/MARKDOWN/TEXT"
APP_VERSION = "1.0.0"

# ===== UTILITY FUNCTIONS =====
get_tesseract_version()     # Runs tesseract --version, returns first line
ensure_dirs()               # Creates TEMP_DIR, UPLOAD_DIR, OUTPUT_DIR
cleanup_temp_dir()          # Deletes TEMP_DIR contents
```

**IMPORTANT for AI Agents:** All paths are relative to `BASE_DIR`. To change any setting (language, DPI, port, format, etc.), modify ONLY this file.

---

### 3.3 `ocr_engine.py` — Tesseract OCR Wrapper

**Class: `OCREngine(language_code)`**

```python
OCREngine("vie")            # Vietnamese only
OCREngine("vie+eng")        # Vietnamese + English

# Methods:
_validate_tesseract()       # Checks tesseract.exe exists and runs
ocr_image(image_path, output_base)
    # Runs: tesseract.exe <image_path> <output_base> -l <lang> --psm 6 --oem 3 --tessdata-dir <path>
    # Reads output_base.txt result
    # Timeout: 120 seconds per image
    # Returns: text string (UTF-8)
    # Cleans up temp .txt file after reading
```

**Tesseract CLI command format:**
```
"C:\...\tesseract.exe" "temp_images\file_page_0001.png" "temp_images\file_page_0001" -l vie --psm 6 --oem 3 --tessdata-dir "C:\...\tessdata"
```

---

### 3.4 `pdf_processor.py` — PDF → Image Converter

**Class: `PDFProcessor(pdf_path)`**

Uses **PyMuPDF (fitz)** to render PDF pages as high-resolution PNG images.

```python
PDFProcessor("path/to/file.pdf")

# Methods:
get_page_count()            # Returns: int (number of pages)
get_file_name()             # Returns: str (filename without extension)
render_page(page_num)       # Renders 1 page at 300 DPI → PNG
                            # Saves to temp_images/{filename}_page_{0001}.png
                            # Returns: path to PNG file
close()                     # Closes the PDF document
```

**DPI calculation:** `zoom = 300 / 72 ≈ 4.17x`

---

### 3.5 `output_generator.py` — Output File Generator

**Class: `OutputGenerator(file_name, output_dir)`**

```python
OutputGenerator("my_pdf", "outputs/")

# Methods:
generate(pages_text[], format)  # Dispatches to format-specific method
                                # Returns: full path to generated file

# Format-specific methods:
_generate_markdown(pages_text)  # *.md with # headings, page breaks with ---
_generate_text(pages_text)      # *.txt with === Trang X === separators
_generate_docx(pages_text)      # *.docx with Times New Roman 13, page breaks,
                                #        heading per page, footer with page count
```

**Output file naming:** `{file_name}_ocr.{ext}`  
Example: `baocao_ocr.docx`, `tailieu_ocr.md`, `vanban_ocr.txt`

---

### 3.6 `index.html` — Web UI (Jinja2 Template)

**Location:** `OCR_App/templates/index.html`  
**Framework:** Bootstrap 5.3 + Bootstrap Icons + Vanilla JS (no framework)

**Layout structure:**
```
┌─────────────────────────────────────────────┐
│ FIXED HEADER (120px, gradient blue)         │
│ ┌──────┐  PHẦN MỀM TỰ ĐỘNG CHUYỂN ĐỔI...   │
│ │ LOGO │  Nhận dạng văn bản tiếng Việt...   │
│ └──────┘                                    │
├─────────────────────────────────────────────┤
│ STEP 1: Chọn file PDF (có thể chọn nhiều)   │
│ ┌─────────────────────────────────────────┐ │
│ │      ☁  Kéo & thả file PDF vào đây      │ │
│ │      [BROWSE...]                        │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ 📄 file1.pdf  120 KB  [✕]              │ │
│ │ 📄 file2.pdf  340 KB  [✕]              │ │
│ │ 📄 file3.pdf  210 KB  [✕]              │ │
│ │ [🗑 Xóa tất cả]                         │ │
│ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ STEP 2: Tùy chọn OCR                        │
│ Ngôn ngữ: [Tiếng Việt ▼]                    │
│ Định dạng: [.docx (Word) ▼]                 │
├─────────────────────────────────────────────┤
│ [🔵 OCR 1 FILE ĐƠN]  [🟡 OCR HÀNG LOẠT]   │
├─────────────────────────────────────────────┤
│ Progress bar (hidden until OCR starts)      │
├─────────────────────────────────────────────┤
│ Results section (hidden until complete):    │
│ - Single file: preview box + download       │
│ - Batch: accordion list per file + ZIP dl   │
├─────────────────────────────────────────────┤
│ FOOTER: Phát triển bởi Nguyễn Khắc Tú -    │
│ Viện KSND khu vực 5 - Bắc Ninh              │
└─────────────────────────────────────────────┘
```

**Key JavaScript functions:**

| Function | Purpose |
|----------|---------|
| `handleFileSelect(event)` | File input change handler, adds to `selectedFiles[]` |
| `addFiles(files)` | Filters PDFs, deduplicates, calls `renderFileList()` |
| `renderFileList()` | Renders file list UI; enables/disables buttons |
| `removeFile(index)` | Removes 1 file from list |
| `clearAllFiles()` | Clears all files + results |
| `startSingleOCR()` | Sends 1st file to `/api/ocr`, displays single result |
| `startBatchOCR()` | Sends all files to `/api/ocr/batch`, displays batch results |
| `showBatchResults(data)` | Renders accordion UI for multiple results |
| `toggleBatchResult(header)` | Toggles accordion open/close |
| `downloadAllZip()` | POSTs file list to `/api/batch/download` → downloads ZIP |
| `copySingleResult()` | Copies single result text to clipboard |

**Button behavior:**
- **OCR 1 FILE ĐƠN** — Enabled when ≥ 1 file selected, uses 1st file
- **OCR HÀNG LOẠT** — Enabled when ≥ 2 files selected, uses all files

---

## 4. DATA FLOW DIAGRAM

```
User selects PDF(s) in browser
        │
        ▼
┌───────────────────┐
│  index.html (JS)  │  FormData: files[] + language + format
│  fetch() POST     │
└───────┬───────────┘
        │ HTTP POST
        ▼
┌───────────────────────────────────────┐
│  main.py  Flask route handler        │
│  /api/ocr  or  /api/ocr/batch        │
└───────┬───────────────────────────────┘
        │
        ├─► Save PDF(s) to uploads/
        │
        ├─► For each PDF:
        │     │
        │     ├─► pdf_processor.py
        │     │   PDFProcessor.render_page(i)
        │     │   → PyMuPDF opens PDF
        │     │   → Renders page at 300 DPI
        │     │   → Saves PNG to temp_images/
        │     │
        │     ├─► ocr_engine.py
        │     │   OCREngine.ocr_image(png, base)
        │     │   → subprocess.run tesseract.exe
        │     │   → Reads output .txt
        │     │   → Returns text string
        │     │
        │     └─► Delete temp PNG
        │
        ├─► output_generator.py
        │   OutputGenerator.generate(pages_text[], format)
        │   → Creates .docx / .md / .txt in outputs/
        │
        ├─► Delete uploaded PDF(s)
        │
        └─► Return JSON response
              │
              ▼
┌───────────────────┐
│  index.html (JS)  │  Renders results
│  User can:        │  - View text preview
│  - Download file  │  - Copy to clipboard
│  - Download ZIP   │  (batch only)
└───────────────────┘
```

---

## 5. DEPENDENCIES

### Python packages (`requirements.txt`):
```
PyMuPDF==1.27.2       # PDF rendering (fitz)
Pillow==11.3.0        # Image processing
python-docx==1.2.0    # Word document generation
Flask==3.1.1          # Web framework
```

### External binary (DO NOT MODIFY):
```
OCR\Tesseract-OCR\tesseract.exe  v5.4.0.20240606
OCR\Tesseract-OCR\tessdata\vie.traineddata
OCR\Tesseract-OCR\tessdata\eng.traineddata
```

### CDN (loaded in browser):
```
Bootstrap 5.3.0 CSS + JS
Bootstrap Icons 1.11.0
```

---

## 6. KEY DESIGN DECISIONS

1. **Why Flask instead of desktop GUI?** — Web UI enables easy integration into other projects, remote access, and modern styling.

2. **Why subprocess Tesseract instead of pytesseract?** — Avoids DLL conflicts. Tesseract portable ships alongside the app.

3. **Why sequential batch processing (not parallel)?** — Tesseract is CPU-heavy; parallel processing would OOM on large PDFs. Sequential is stable.

4. **Why 300 DPI?** — Optimal balance of OCR accuracy vs. file size. Lower = worse accuracy, higher = slower.

5. **PSM 6 (Unified block of text)?** — Best for scanned documents with uniform text blocks. Not suitable for sparse/diagram-heavy pages.

6. **All config in config.py?** — Single source of truth. An AI agent only needs to read this one file to understand all adjustable parameters.

---

## 7. INTEGRATION GUIDE (for AI Agents)

### To embed this app into another project:

```python
# 1. Import the OCR pipeline directly (bypass Flask):
from OCR_App.ocr_engine import OCREngine
from OCR_App.pdf_processor import PDFProcessor
from OCR_App.output_generator import OutputGenerator

# 2. Process a PDF programmatically:
engine = OCREngine("vie")
pdf = PDFProcessor("path/to/file.pdf")
texts = []
for i in range(pdf.get_page_count()):
    img = pdf.render_page(i)
    text = engine.ocr_image(img, img.replace(".png", ""))
    texts.append(text)
pdf.close()

gen = OutputGenerator(pdf.get_file_name(), "outputs/")
output_path = gen.generate(texts, "docx")
```

### Key integration points:
- **config.py** → Change `BASE_DIR` logic if embedding in different directory
- **ocr_engine.py** → Core OCR, can be used standalone
- **pdf_processor.py** → PDF rendering, can be used standalone
- **output_generator.py** → Output generation, can be used standalone
- **main.py** → Flask routes, can be mounted as Blueprint in parent app

---

## 8. CHANGELOG

| Date | Version | Changes |
|------|---------|---------|
| 2026-07-13 | 1.0.0 | Initial Flask web app |
| 2026-07-13 | 1.0.1 | Added `logo_moi.png` in header |
| 2026-07-13 | 1.0.2 | Changed app title to "PHẦN MỀM TỰ ĐỘNG CHUYỂN ĐỔI PDF SANG WORD/MARKDOWN/TEXT" |
| 2026-07-13 | 1.0.3 | Updated footer: "Phát triển bởi Nguyễn Khắc Tú - Viện KSND khu vực 5 - Bắc Ninh" |
| 2026-07-13 | 1.1.0 | **Batch OCR**: Added `/api/ocr/batch`, `/api/batch/download`, multi-file UI, ZIP download |
| 2026-07-13 | 1.1.0 | Fixed UnicodeEncodeError in main.py for Vietnamese console output |
| 2026-07-13 | 1.1.0 | Complete PROJECT.md rewrite for AI/LLM readability |