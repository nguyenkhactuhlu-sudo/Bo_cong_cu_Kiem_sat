<!-- 
  ╔══════════════════════════════════════════════════════════════╗
  ║  AI_README_FIRST                                            ║
  ║  >>> ĐÂY LÀ FILE MÔ TẢ CẤU TRÚC DỰ ÁN <<<                   ║
  ║  Khi bạn là một AI agent được giao nhiệm vụ làm việc với    ║
  ║  mã nguồn này, hãy ĐỌC TOÀN BỘ FILE NÀY TRƯỚC TIÊN.        ║
  ║  File này chứa tổng quan kiến trúc, danh sách công cụ,      ║
  ║  port mapping, pattern thêm tool mới, và các ghi chú kỹ    ║
  ║  thuật quan trọng.                                          ║
  ╚══════════════════════════════════════════════════════════════╝
-->

# BỘ CÔNG CỤ NGHIỆP VỤ – VIỆN KIỂM SÁT NHÂN DÂN

> **Mục đích file này:** Giúp AI nắm tổng quan dự án nhanh, tiết kiệm token.
> **Tác giả:** Nguyễn Khắc Tú – Viện KSND KV5 Bắc Ninh

---

## 1. TỔNG QUAN

- **Loại dự án:** Web dashboard tập hợp các công cụ nghiệp vụ kiểm sát
- **Frontend:** HTML/CSS/JS (thuần, không framework), file chính `index.html`
- **Backend GUI tools:** Python Flask (HTML template inline trong file `.py`), đóng gói `.exe` bằng PyInstaller
- **Deploy:** GitHub Pages (static) + file `.exe` / `.zip` tải về cho tool offline
- **Port mapping:** Mỗi tool Flask chạy trên port riêng để tránh xung đột:
  - FileRenamer: **5789**
  - DocxToMd: **5788**
  - PdfToMd: **tự động** (5100+)

---

## 2. CẤU TRÚC THƯ MỤC GỐC

```
Bo_cong_cu_Kiem_sat/
├── STRUCTURE.md                  ← File này (AI ĐỌC TRƯỚC TIÊN)
├── index.html                    ← Dashboard chính
├── .gitignore
│
├── static/                       ← Ảnh, tài nguyên tĩnh
│   ├── logo_moi.png
│   └── Nen.jpg
│
├── Data/                         ← Công cụ tĩnh (HTML) + tài liệu
│   ├── TinhTuoiThoiHan.html
│   ├── HuongDan.html
│   ├── Slide.html
│   ├── slide.docx
│   ├── slide.md
│   └── Recording.mp4
│
└── Tool/                         ← Các công cụ Python GUI (có thể build .exe)
    ├── auto_install.py           ← Module dùng chung: tự động kiểm tra & cài thư viện thiếu
    ├── App_DS/                   ← Tính án phí (HTML standalone)
    │   └── index.html            ← Công cụ tính án phí
    │
    ├── App_tinh_lai_suat/        ← Tính lãi suất (HTML standalone)
    │   └── index.html            ← Công cụ tính lãi suất
    │
    ├── DocxToMd/                 ← Word (.doc/.docx) → Markdown
    │   ├── convert_doc_to_md.py  ← Engine chuyển đổi (python-docx + win32com)
    │   ├── docx_to_md_gui.py     ← Flask GUI (port 5788)
    │   ├── DocxToMdGUI.spec      ← PyInstaller spec
    │   ├── DocxToMdGUI.exe       ← GUI standalone
    │   ├── Docxtomd.zip          ← File phân phối (tải về từ index.html)
    │   ├── index.html            ← Trang giới thiệu + nút tải .zip
    │   └── HuongDanSuDung.txt
    │
    ├── PdfToMd/                  ← PDF / Ảnh → Markdown
    │   ├── pdf_to_md.py          ← Engine OCR (Gemini API + pypdf)
    │   ├── pdf_to_md_gui.py      ← Flask GUI (port tự động 5100+)
    │   ├── PdfToMdGUI.spec       ← PyInstaller spec
    │   ├── PdfToMdGUI.exe        ← GUI standalone (trong dist/)
    │   ├── PdfToMd.zip           ← File phân phối (~50MB, tải về từ index.html)
    │   ├── index.html            ← Trang giới thiệu + nút tải .zip
    │   ├── API keys.txt          ← Hướng dẫn lấy Gemini API Key
    │   └── HuongDanSuDung.txt
    │
    ├── AnDanh/                   ← Ẩn danh văn bản (HTML app)
    │   ├── index.html            ← Công cụ ẩn danh
    │   ├── AnDanhTool.exe        ← Bản standalone
    │   ├── AnDanhTool.zip        ← File phân phối
    │   └── HuongDanSuDung.txt
    │
    └── FileRenamer/              ← Đổi tên file hàng loạt
        ├── file_renamer.py       ← Engine chuẩn hóa tên file
        ├── file_renamer_gui.py   ← Flask GUI (port 5789)
        ├── FileRenamerGUI.spec   ← PyInstaller spec (GUI)
        ├── FileRenamerGUI.exe    ← GUI standalone
        ├── FileRenamer.exe       ← CLI standalone
        ├── FileRenamer.zip       ← File phân phối
        ├── index.html            ← Trang giới thiệu + nút tải .zip
        └── HuongDanSuDung.txt
```

---

## 3. DANH SÁCH CÔNG CỤ

### 3.1. Tính lãi suất
| Thuộc tính | Giá trị |
|---|---|
| **ID** | `tinh-lai-suat` |
| **Loại** | Static HTML (iframe) |
| **URL** | `Tool/App_tinh_lai_suat/index.html` |
| **Accent** | `accent-sky` |

### 3.2. Tính án phí
| Thuộc tính | Giá trị |
|---|---|
| **ID** | `tinh-an-phi` |
| **Loại** | Static HTML (iframe) |
| **URL** | `Tool/App_DS/index.html` |
| **Accent** | `accent-bronze` |

### 3.3. Kiểm sát Bản án (bản dùng chung)
| Thuộc tính | Giá trị |
|---|---|
| **ID** | `kiem-sat-ban-an-chung` |
| **Loại** | Web app external (iframe) |
| **URL** | `https://udify.app/chat/FoGbxKbFMFZSylhe` |
| **Accent** | `accent-plum` |

### 3.4. Kiểm sát Bản án (bản nâng cấp)
| Thuộc tính | Giá trị |
|---|---|
| **ID** | `kiem-sat-ban-an-nang-cao` |
| **Loại** | Web app external (iframe) |
| **URL** | `https://udify.app/chat/Ho3TdpoYQ9OjTbIq` |
| **Accent** | `accent-plum` |
| **Ghi chú** | Dành riêng Viện KSND KV5 Bắc Ninh |

### 3.5. Hỏi đáp AI – Hình sự & Tố tụng hình sự
| Thuộc tính | Giá trị |
|---|---|
| **ID** | `notebook-lm` |
| **Loại** | External link, mở tab mới (`newTab: true`) |
| **URL** | `https://notebooklm.google.com/notebook/af52b719-3125-4b4e-aaad-93432843b0ee` |
| **Accent** | `accent-sky` |

### 3.6. Tính tuổi – Tính thời hạn – Đếm tạm giữ
| Thuộc tính | Giá trị |
|---|---|---|
| **ID** | `tinh-tuoi-thoi-han` |
| **Loại** | Static HTML (iframe) |
| **URL** | `Data/TinhTuoiThoiHan.html` |
| **Accent** | `accent-sky` |
| **Chức năng** | Tính tuổi, tính thời hạn tố tụng (Điều 135 BLTTHS), đếm thời gian tạm giữ (Điều 117 BLTTHS) |
| **Sửa lỗi** | Đã sửa lỗi lệch ngày: thời hạn tính từ ngày tiếp theo của ngày xác định sự kiện |
| **Tính năng mới** | Thêm phần đếm thời gian tạm giữ với cảnh báo màu (đỏ < 6h, vàng < 24h) |

### 3.7. Hướng dẫn tạo sơ đồ tư duy tự động
| Thuộc tính | Giá trị |
|---|---|
| **ID** | `huong-dan-so-do-tu-duy` |
| **Loại** | Static HTML (iframe) |
| **URL** | `Data/HuongDan.html` |
| **Accent** | `accent-bronze` |

### 3.8. Ẩn danh văn bản (che thông tin)
| Thuộc tính | Giá trị |
|---|---|
| **ID** | `an-danh-tool` |
| **Loại** | HTML app (iframe) |
| **URL** | `Tool/AnDanh/index.html` |
| **Accent** | `accent-plum` |
| **Ghi chú** | Phát triển bởi Trần Huy – Viện KSND KV11 Đắk Lắk |

### 3.9. File Renamer – Đổi tên file hàng loạt
| Thuộc tính | Giá trị |
|---|---|
| **ID** | `file-renamer-tool` |
| **Loại** | Python Flask GUI → `.exe` standalone |
| **URL** | `Tool/FileRenamer/index.html` |
| **Accent** | `accent-sky` |
| **Files** | `Tool/FileRenamer/file_renamer.py`, `Tool/FileRenamer/file_renamer_gui.py` |
| **Port** | 5789 |
| **Backend** | Flask + ctypes native Windows folder browser |
| **Đặc điểm** | 1 file `.py` chứa cả backend lẫn HTML template inline; quét đệ quy; xem trước trước khi đổi tên; **click vào tên mới (màu xanh) để tự đặt tên file tùy chỉnh**, hỗ trợ khôi phục tên đề xuất |
| **File phân phối** | `FileRenamer.zip` (chứa `FileRenamerGUI.exe`) |

### 3.10. DocxToMd – Word (.doc/.docx) sang Markdown
| Thuộc tính | Giá trị |
|---|---|
| **ID** | `docx-to-md-tool` |
| **Loại** | Python Flask GUI → `.exe` standalone |
| **URL** | `Tool/DocxToMd/index.html` |
| **Accent** | `accent-bronze` |
| **Files** | `Tool/DocxToMd/docx_to_md_gui.py`, `Tool/DocxToMd/convert_doc_to_md.py` |
| **Port** | 5788 |
| **Engine** | python-docx (`.docx`) + win32com (`.doc` qua MS Word) |
| **Yêu cầu** | Windows + Microsoft Word (cho file `.doc`) |
| **Đặc điểm** | Quét đệ quy thư mục, tạo file `.md` cùng tên bên cạnh file gốc, giữ nguyên file gốc |
| **File phân phối** | `Docxtomd.zip` (chứa `DocxToMdGUI.exe`) |

### 3.11. PdfToMd – PDF/Ảnh sang Markdown
| Thuộc tính | Giá trị |
|---|---|
| **ID** | `pdf-to-md-tool` |
| **Loại** | Python Flask GUI → `.exe` standalone |
| **URL** | `Tool/PdfToMd/index.html` |
| **Accent** | `accent-sky` |
| **Files** | `Tool/PdfToMd/pdf_to_md_gui.py`, `Tool/PdfToMd/pdf_to_md.py`, `Tool/PdfToMd/PdfToMdGUI.spec` |
| **Port** | Tự động (5100+) |
| **Engine** | Gemini 2.5 Flash API (OCR) + pypdf (PDF có text) |
| **Yêu cầu** | Gemini API Key (người dùng tự lấy tại Google AI Studio) |
| **Đặc điểm** | Hỗ trợ `.pdf`, `.jpg`, `.png`, `.tiff`, `.bmp`, `.gif`, `.webp`; anti-hallucination (fuzzy check); async concurrent với asyncio |
| **File phân phối** | `PdfToMd.zip` (~50MB, chứa `PdfToMdGUI.exe`) |

---

## 4. PATTERN CHUNG – CÁCH THÊM TOOL GUI MỚI

```
1. Tạo thư mục Tool/<TenTool>/
2. File <ten>_gui.py ← Flask backend + toàn bộ HTML/CSS/JS template inline
3. File engine.py ← Logic xử lý chính
4. File index.html ← Trang giới thiệu + link tải .exe
5. File HuongDanSuDung.txt ← Hướng dẫn sử dụng
6. File *.spec ← PyInstaller spec (nếu cần build .exe)
7. File .exe / .zip ← File phân phối (nén .exe thành .zip để tránh bị chặn)
8. Thêm entry vào TOOLS array trong index.html
```

**Template TOOLS entry:**
```js
{
    id: 'tool-id',
    label: 'CÔNG CỤ',
    title: 'Tên công cụ',
    subtitle: 'Mô tả ngắn',
    url: 'Tool/TenTool/index.html',
    accent: 'accent-sky'  // hoặc accent-bronze, accent-plum
}
```

**Template PyInstaller spec:**
```python
a = Analysis(
    ['<ten>_gui.py'],
    datas=[('<engine>.py', '.')],
    hiddenimports=[],
)
exe = EXE(pyz, a.scripts, ..., name='TenToolGUI', console=True, ...)
```

---

## 5. DASHBOARD CHÍNH (`index.html`)

- **TOOLS array** (dòng ~821-908) định nghĩa tất cả công cụ
- Mỗi tool có: `id`, `label`, `title`, `subtitle`, `url`, `accent`, `newTab` (optional)
- `accent-sky` = xanh, `accent-bronze` = vàng, `accent-plum` = đỏ tím
- `newTab: true` → mở tab mới. Mặc định → mở trong iframe workspace
- Card `disabled` cuối danh sách dành cho công cụ sắp ra mắt
- URL tool local: `Tool/<TenTool>/index.html`
- Khi user bấm vào card tool, iframe workspace sẽ mở `index.html` của tool đó, trang này có nút "TẢI XUỐNG" để tải file `.zip` chứa `.exe`

---

## 6. GHI CHÚ KỸ THUẬT

| Mục | Chi tiết |
|---|---|
| **Python version** | 3.14 (Windows, portable: `C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64`) |
| **PyInstaller** | Đã cài, dùng `python -m PyInstaller xxx.spec` |
| **Build .exe** | `console=True`, `upx=True`, `--clean --noconfirm` |
| **File .exe → .zip** | Nén lại để tránh bị trình duyệt/antivirus chặn khi tải |
| **Deploy** | GitHub Pages phục vụ file tĩnh; file `.zip` >50MB nên dùng Git LFS nếu cần |
| **Folder Browser** | Dùng `ctypes.windll.shell32.SHBrowseForFolderW` (native Windows, không phụ thuộc tkinter) |
| **Auto-install library** | Mỗi tool GUI dùng module chung `Tool/auto_install.py` để tự động kiểm tra & cài thư viện thiếu khi chạy file `.py` |
| **File .zip** | File `.zip` phân phối (trong `Tool/*/`) được push lên Git để người dùng tải về qua GitHub Pages; file `.zip` trong `build/` và `dist/` bị `.gitignore` chặn |

---

## 7. PORT MAPPING (TRÁNH XUNG ĐỘT)

| Tool | Port | Cơ chế |
|---|---|---|
| FileRenamer GUI | **5789** | Cố định |
| DocxToMd GUI | **5788** | Cố định |
| PdfToMd GUI | **5100+ tự động** | `find_free_port()` |

> **Quan trọng:** Không để 2 tool dùng chung 1 port. PdfToMd dùng `socket.bind()` để tìm port trống, an toàn nhất.

---

## 8. QUY ƯỚC CHO AI AGENT

Khi một AI agent được giao nhiệm vụ làm việc với mã nguồn này:

1. **Đọc file này đầu tiên** (`STRUCTURE.md`) — nó chứa toàn bộ kiến trúc và quy ước
2. Không thay đổi port của các tool đã có
3. Không commit file `.exe`, `.zip`, `build/`, `dist/`, `__pycache__/` (đã `.gitignore`)
4. Khi thêm tool mới: theo đúng pattern ở mục 4
5. Cập nhật file này sau khi thay đổi cấu trúc dự án