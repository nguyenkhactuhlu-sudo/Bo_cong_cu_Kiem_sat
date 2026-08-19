# Cấu trúc hệ thống — Bộ công cụ nghiệp vụ Kiểm sát

> Cập nhật: 19/08/2026. Tài liệu này phản ánh mã nguồn đang tồn tại trong repository.

## 1. Tổng quan

Dự án có hai bề mặt sử dụng chung mã nghiệp vụ:

1. **Dashboard web** tại `index.html`, triển khai như website tĩnh. Dashboard bento chia công cụ thành nhóm ngoại tuyến và trực tuyến/AI; công cụ nội bộ mở trong iframe, liên kết ngoài mở theo cấu hình từng card.
2. **Bộ desktop offline** tại `DesktopOffline/`, dùng Python + Flask cục bộ + pywebview/WebView2. Người dùng nhận một file cài đặt; máy đích không cần Python, pip, Chrome/Edge hay Internet.

Mã nguồn trong `Tool/`, `Data/` và `static/` là nguồn chuẩn. Quy trình desktop sao chép các phần cần thiết vào `DesktopOffline/stage/payload`, thay CDN bằng tài nguyên cục bộ và đóng gói; không sửa ngược mã nguồn trong bước staging.

## 2. Sơ đồ thư mục hiện tại

```text
Bo_cong_cu_Kiem_sat/
├── index.html                     Dashboard web chính và danh sách TOOLS
├── STRUCTURE.md                   Tài liệu kiến trúc này
├── TASK.md                        Ghi chép/yêu cầu phát triển
├── qa_download_packages.py        Script tải/nhận gói (QA download)
├── static/
│   ├── logo_moi.png               Logo dùng chung
│   ├── Nen.jpg                    Ảnh nền
│   ├── lotus.png                  Ảnh nền hoa sen (dashboard/launcher)
│   └── tool-page-theme.css        Theme trang giới thiệu công cụ
├── Data/
│   ├── TinhTuoiThoiHan.html       Tính tuổi, thời hạn, tạm giữ/tạm giam
│   ├── HuongDan.html              Hướng dẫn tạo sơ đồ tư duy
│   ├── Slide.html                 Slide nhúng
│   └── slide.docx, slide.md, Recording.mp4
├── Tool/
│   ├── auto_install.py            Hỗ trợ dependency cho bản chạy nguồn cũ
│   ├── App_tinh_lai_suat/         Flask + HTML tự động tính tiền lãi
│   ├── App_DS/                    Flask + HTML tính án phí
│   ├── AnDanh/
│   │   ├── index.html             Trang giới thiệu web
│   │   ├── andanh_app/            Flask, detector và xử lý DOCX
│   │   ├── AnDanhTool.zip         Bản đóng gói portable
│   │   ├── build_portable.ps1     Script đóng gói portable
│   │   └── HuongDanSuDung.txt     Hướng dẫn sử dụng
│   ├── FileRenamer/               Engine + Flask GUI đổi tên hàng loạt
│   │   ├── file_renamer.py        Engine quét/sinh tên
│   │   ├── file_renamer_gui.py    Flask GUI + API scan/execute
│   │   ├── index.html             Trang giới thiệu web
│   │   ├── FileRenamer.zip        Bản đóng gói portable
│   │   ├── build_portable.ps1     Script đóng gói portable
│   │   └── qa_folder_dialog.py    QA kiểm tra hộp thoại thư mục
│   ├── OCR_PDF_Tool/
│   │   ├── index.html             Trang giới thiệu web
│   │   ├── source/                Flask, PyMuPDF, Tesseract, xuất DOCX/MD/TXT
│   │   ├── OCR_PDF_Tool.zip       Bản đóng gói portable
│   │   ├── OCR_PDF_Tool/          Thư mục EXE portable đã giải nén
│   │   └── HuongDanSuDung.txt     Hướng dẫn sử dụng
│   ├── SpellChecker/              Flask, engine chính tả và xử lý Word
│   │   ├── app.py                 Flask app
│   │   ├── engine.py              Phát hiện lỗi chính tả
│   │   ├── docx_processor.py      Xử lý Word DOCX
│   │   ├── word_converter.py      Chuyển .doc cũ sang .docx
│   │   ├── index.html             Trang giới thiệu web
│   │   ├── data/vi.dic           Từ điển tiếng Việt
│   │   └── tests/                 Unit test
│   ├── ThuLyAnDS/                 Trang giới thiệu công cụ cần mạng/Gemini
│   └── _local_archive/            Dữ liệu lưu trữ cục bộ (vd: DocxToMd), không phải runtime chính
├── Gioi_thieu_BCC/
│   └── SKKN_BCCVKS.docx           Hồ sơ/báo cáo sáng kiến (đề nghị công nhận)
├── dist/                          Đầu ra build (thư mục chung)
├── tmp/                           Thư mục tạm
└── DesktopOffline/
    ├── main.py                    Launcher, cửa sổ tool và API native
    ├── tool_registry.py           Registry 7 công cụ desktop (interest, court_fee, deadline, anonymizer, renamer, spell_checker, ocr)
    ├── prepare_payload.py         Staging, local hóa asset, tích hợp Save As
    ├── brand.css                  Font/theme áp dụng cho payload
    ├── make_icon.py               Tạo icon
    ├── BoCongCuOffline.spec       PyInstaller spec
    ├── installer.iss              Inno Setup: một file cài đặt
    ├── build.ps1                  Pipeline build đầy đủ
    ├── README.md                  Tài liệu desktop
    ├── requirements-build.txt     Dependency build
    ├── vendor/                    WebView2, font, icon và thư viện giao diện
    ├── stage/payload/             Bản sao phát hành được sinh tự động
    ├── dist/app/                  EXE ứng dụng + Tesseract trước khi cài đặt
    ├── dist/BoCongCuKiemSat_Offline_Setup.exe
    ├── qa_*.py, capture_ui.ps1    Kiểm thử phát hành
    ├── .build-venv/               Môi trường ảo build
    └── build/, dist/, qa/, tmp/   Đầu ra build/kiểm thử tạm
```

Các thư mục `build/`, `dist/`, `stage/`, `vendor/`, `__pycache__/` là đầu ra hoặc tài nguyên build, không phải nơi sửa logic nghiệp vụ gốc.

## 3. Dashboard web

`index.html` chứa mảng JavaScript `TOOLS`; mỗi phần tử có các trường chính: `id`, `group`, `span`, `badge`, `badgeClass`, `title`, `desc`, `illust`, `url`, `accent`, `footer`, `newTab`.

### Công cụ ngoại tuyến (7 công cụ)

| ID web | Công cụ | Chức năng chính | Nguồn/chế độ |
|---|---|---|---|
| `tinh-lai-suat` | Tự động tính tiền lãi | Tính tiền lãi trong hạn, quá hạn, chậm trả trong giao dịch dân sự | `Tool/App_tinh_lai_suat/index.html` |
| `tinh-an-phi` | Tính án phí | Tra cứu và tính nhanh án phí hình sự, dân sự | `Tool/App_DS/index.html` |
| `tinh-tuoi-thoi-han` | Tính tuổi — thời hạn | Tính tuổi, ngày giờ, kiểm soát tạm giữ, tạm giam tố tụng | `Data/TinhTuoiThoiHan.html` |
| `an-danh-tool` | Tự động che thông tin | Ẩn thông tin cá nhân trong văn bản trước khi công bố/giao AI | Trang `Tool/AnDanh/index.html`; Flask `andanh_app/` |
| `file-renamer-tool` | Tự động đổi tên file | Đổi tên hàng loạt, chuẩn hóa Unicode, xem trước | Trang + Flask/engine `Tool/FileRenamer/` |
| `spell-checker-tool` | Rà soát chính tả Word | Phát hiện lỗi chính tả, cụm từ nghiệp vụ, khoảng trắng, dấu câu; xuất Word tô vàng/bản đã sửa | Trang + Flask/engine `Tool/SpellChecker/` |
| `ocr-pdf-tool` | Nhận dạng chữ PDF/ảnh | Trích xuất chữ từ PDF/ảnh không cần mạng, xuất Word/Markdown/TXT | Trang + Flask/Tesseract `Tool/OCR_PDF_Tool/source/` |

### Công cụ trực tuyến/AI (5 công cụ)

| ID web | Công cụ | Chức năng chính | Ghi chú |
|---|---|---|---|
| `kiem-sat-ban-an-chung` | Kiểm sát bản án — bản dùng chung | Đối chiếu phát hiện lỗi chính tả, mâu thuẫn, vi phạm, thiếu sót bản án HS/DS | Liên kết Udify |
| `kiem-sat-ban-an-nang-cao` | Kiểm sát bản án — bản chuyên biệt | Bản nâng cấp tối ưu riêng cho VKS KV5 | Liên kết Udify |
| `notebook-lm` | Hình sự & tố tụng hình sự | Tra cứu điều luật, hỗ trợ lập luận tố tụng từ kho tri thức | Mở NotebookLM tab mới |
| `huong-dan-so-do-tu-duy` | Hướng dẫn tạo sơ đồ tư duy | Thao tác chi tiết + bộ prompt mẫu tạo sơ đồ tư duy tự động | Nội dung local; quy trình đích cần dịch vụ AI |
| `thu-ly-an-ds` | Quản lý thông báo thụ lý vụ án | Đọc PDF scan, nhận diện thông tin vụ án/đương sự bằng Gemini | Cần mạng (sử dụng Gemini) |

Dashboard tổng là nơi duy nhất hiển thị chữ ký phát triển. Các công cụ con không chứa chữ ký riêng.

## 4. Kiến trúc desktop offline

### 4.1. Luồng chạy

```text
Launcher WebView2 (main.py)
  ├─ trang launcher và nền `static/lotus.png` được phục vụ qua 127.0.0.1
  └─ người dùng chọn tool
      └─ tạo process BoCongCuOffline.exe --tool <id> (ẩn console)
          ├─ Flask chỉ bind 127.0.0.1 trên cổng trống
          ├─ pywebview mở cửa sổ riêng, không thanh địa chỉ
          └─ ToolApi cung cấp chọn thư mục và Save As native
```

`tool_registry.py` đăng ký 7 ID desktop: `interest`, `court_fee`, `deadline`, `anonymizer`, `renamer`, `spell_checker`, `ocr`.

### 4.2. Phụ thuộc đi kèm bộ cài

- Python runtime và thư viện được PyInstaller đóng vào `BoCongCuOffline.exe`.
- WebView2 Fixed Version x64 nằm cạnh ứng dụng tại `runtime/WebView2`.
- Tesseract portable và dữ liệu ngôn ngữ `vie`, `eng` nằm tại `Tesseract-OCR`.
- Be Vietnam Pro Regular/SemiBold/Bold, Font Awesome, Bootstrap và Bootstrap Icons được lưu cục bộ.
- Microsoft Word chỉ cần cho việc chuyển `.doc` cũ sang `.docx`; `.docx` không cần COM để đọc/ghi.
- `vendor/` lưu tài nguyên giao diện, font và WebView2 dùng cho payload.
- `make_icon.py` tạo icon ứng dụng trong quá trình build.

### 4.3. Build và phát hành

```powershell
powershell -ExecutionPolicy Bypass -File .\DesktopOffline\build.ps1
```

Pipeline: kiểm tra/tải vendor trên máy build → tạo payload → chạy QA → PyInstaller → chép Tesseract → Inno Setup. Đầu ra cho người dùng là:

`DesktopOffline/dist/BoCongCuKiemSat_Offline_Setup.exe`

## 5. Hỗ trợ đường dẫn Unicode tiếng Việt

Tất cả luồng chọn file/thư mục của bản phát hành phải hỗ trợ đường dẫn và tên tiếng Việt có dấu.

| Công cụ | Đầu vào | Cơ chế bảo đảm |
|---|---|---|
| FileRenamer | Thư mục, cây file | `FolderBrowserDialog` của Windows chạy trong tiến trình STA ẩn; kết quả trả về UTF-8; backend dùng `pathlib.Path`; JSON/Flask UTF-8 |
| AnDanh | `.docx` | Browser/WebView upload; tên tạm UUID ASCII; `python-docx` đọc/ghi file tạm |
| SpellChecker | `.doc`, `.docx` | Tên hiển thị Unicode được giữ cho đầu ra; file tạm UUID ASCII; Word COM nhận đường dẫn tuyệt đối Unicode |
| OCR | `.pdf`, một hoặc nhiều file | Tên gốc Unicode giữ cho file kết quả; PDF/ảnh trung gian dùng UUID ASCII để tương thích Tesseract |

Không truyền đường dẫn bằng chuỗi lệnh shell. Khi gọi subprocess phải dùng danh sách đối số. Không dùng `encode/decode` thủ công cho đường dẫn. Kiểm thử bắt buộc: `DesktopOffline/qa_unicode_paths.py`.

## 6. Mô-đun nghiệp vụ chính

- **App_tinh_lai_suat:** `tinh_lai.py` + `app.py` tự động tính tiền lãi theo Nghị quyết 01/2019/NQ-HĐTP.
- **App_DS:** `app.py` tính/tra cứu án phí hình sự, dân sự.
- **AnDanh:** `app.py` nhận/xuất DOCX; `docx_io.py` đọc và thay thế trong đoạn, bảng, header/footer; `detector.py` phát hiện dữ liệu cá nhân.
- **FileRenamer:** `file_renamer.py` quét và sinh tên; `file_renamer_gui.py` cung cấp API scan/execute và giao diện xem trước. Luôn xem trước, không tự đổi tên khi chưa xác nhận.
- **SpellChecker:** `engine.py` phát hiện lỗi; `docx_processor.py` xuất bản đánh dấu/bản sửa; `word_converter.py` dùng phiên Word riêng cho `.doc`. Dữ liệu từ điển tiếng Việt tại `data/vi.dic`.
- **OCR:** `pdf_processor.py` render PDF bằng PyMuPDF; `ocr_engine.py` gọi Tesseract không hiện CMD; `output_generator.py` tạo DOCX/Markdown/TXT; `main.py` xử lý đơn lẻ, hàng loạt và download ZIP.
- **ThuLyAnDS:** `index.html` trang giới thiệu; công cụ dùng Gemini API để đọc PDF scan, nhận diện vụ án/đương sự, quản lý hồ sơ, ghi sổ Excel và soạn văn bản kiểm sát theo mẫu. (Cần kết nối mạng)

## 7. Kiểm thử quan trọng

```powershell
$env:PYTHONIOENCODING='utf-8'
& .\DesktopOffline\.build-venv\Scripts\python.exe .\DesktopOffline\prepare_payload.py
& .\DesktopOffline\.build-venv\Scripts\python.exe .\DesktopOffline\qa_unicode_paths.py
& .\DesktopOffline\.build-venv\Scripts\python.exe .\DesktopOffline\qa_choose_folder.py
& .\DesktopOffline\.build-venv\Scripts\python.exe .\DesktopOffline\qa_ocr_save_as.py
& .\DesktopOffline\.build-venv\Scripts\python.exe .\DesktopOffline\qa_save_as.py
& .\DesktopOffline\.build-venv\Scripts\python.exe .\DesktopOffline\qa_ui_behavior.py
```

Ngoài ra chạy unit test trong `Tool/SpellChecker/tests/` và `Tool/AnDanh/andanh_app/tests/`. `qa_ui_assets.py` kiểm tra tài nguyên local, logo, font và không còn CDN trong payload.

## 8. Quy ước bảo trì

1. Sửa logic ở `Tool/`, `Data/`, `static/` trước; chạy lại `prepare_payload.py`, không sửa tay `stage/payload`.
2. Mọi công cụ cần file/thư mục phải có kiểm thử tên Unicode tiếng Việt.
3. Desktop chỉ bind `127.0.0.1`, không thêm phụ thuộc mạng cho công cụ offline.
4. Không thêm chữ ký vào công cụ con; chỉ dashboard tổng có chữ ký.
5. Không commit cache/build tạm. Không xóa hay ghi đè thay đổi khác trong worktree.
6. Khi thêm tool desktop, cập nhật `tool_registry.py`, `prepare_payload.py`, PyInstaller hidden imports/datas, QA và tài liệu này.
7. Khi thêm card web, cập nhật mảng `TOOLS` trong `index.html` và phân nhóm online/offline đúng khả năng kết nối.
8. Nền dashboard dùng `static/lotus.png` neo ở chân trang và phủ gradient để hòa phần trên ảnh; launcher desktop phải phục vụ ảnh qua Flask cục bộ, không nhúng base64 ảnh lớn vào HTML.
