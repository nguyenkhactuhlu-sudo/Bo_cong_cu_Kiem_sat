# Công cụ ẨN DANH văn bản (sử dụng nội bộ)

Công cụ tự động ẩn danh **tên người, số điện thoại, CCCD/CMND, địa chỉ** trong file Word `.docx`. Chạy 100% trên máy tính của bạn — không gửi dữ liệu ra mạng.

## Cấu trúc thư mục

```
andanh_app/
├── app.py              ← Flask web server
├── detector.py         ← Module phát hiện PII
├── docx_io.py          ← Module đọc/ghi DOCX (giữ định dạng)
├── requirements.txt    ← Thư viện cần
├── run.bat             ← Chạy trực tiếp (cần Python)
├── build_exe.bat       ← Build file .exe (chạy 1 lần)
├── tests/              ← Kiểm thử nhận diện và xuất DOCX
└── README.md
```

## Cách sử dụng

### Cách 1: Chạy nhanh (cần cài Python)

1. Cài Python 3.10+ từ python.org (nhớ tích **Add Python to PATH**)
2. Mở folder `andanh_app`, double-click `run.bat`
3. Trình duyệt tự mở tại `http://127.0.0.1:5000`

### Cách 2: Build file `.exe` (1 lần duy nhất)

1. Cài Python 3.10+ một lần
2. Double-click `build_exe.bat` — chờ vài phút
3. File `dist\AnDanhTool.exe` được tạo. Copy file này đi đâu cũng chạy được, **không cần Python**.

### Quy trình ẩn danh (3 bước)

1. **Bước 1 — Tải file**: Chọn file `.docx` cần ẩn danh, bấm **Ẩn danh**
2. **Bước 2 — Kiểm tra**: Tool quét tự động và hiển thị bảng:
   - Tên người theo danh xưng/ngữ cảnh hoặc họ Việt Nam phổ biến
   - Số điện thoại / CCCD / CMND
   - Địa chỉ
   
   Bạn có thể:
   - Bỏ tích các dòng KHÔNG cần ẩn (false positive)
   - Sửa cột "Tên ẩn danh" theo ý muốn
   - Nhập thêm cụm từ chưa được nhận diện và nội dung thay thế tương ứng
3. **Bước 3 — Xuất file**: Bấm **Xuất file đã ẩn danh** → tải file `.docx` mới (giữ nguyên định dạng).

## Bảo mật

- ✅ Toàn bộ xử lý chạy local trên `127.0.0.1` (chỉ máy bạn truy cập)
- ✅ Không có gọi mạng ra ngoài
- ✅ Không lưu log
- ✅ File xuất tạm được xoá sau khi gửi về trình duyệt

## Quy tắc phát hiện

**Tên người:**
- Cụm 2-5 từ sau danh xưng/vai trò như `ông`, `bà`, `bị cáo`, `nguyên đơn`, `họ và tên`...
- Cụm 2-5 từ bắt đầu bằng một họ Việt Nam phổ biến
- Không quét mù mọi cụm viết hoa; bỏ qua tiêu đề, cơ quan và tên nằm trong địa chỉ
- Hai tên gần giống vẫn được giữ riêng; chỉ loại kết quả trùng hoàn toàn hoặc phần thừa của tên dài hơn

**Số điện thoại:** `0xxxxxxxxx`, `+84xxxxxxxxx`, có thể chứa dấu cách/chấm/gạch ngang

**CCCD:** 12 số liên tiếp (không nằm trong số tiền)

**CMND:** 9 số liên tiếp (không nằm trong số tiền)

**Địa chỉ:** Cụm từ sau `trú tại`, `địa chỉ`, `thường trú`, `HKTTT`...

**Thông tin tự thêm:** Người dùng có thể nhập bất kỳ cụm chính xác nào trong tài liệu và nội dung muốn thay thế. Cụm dài được thay trước; việc thay thế hoạt động cả khi Word chia nội dung qua nhiều `run`, trong bảng, đầu trang và chân trang.
