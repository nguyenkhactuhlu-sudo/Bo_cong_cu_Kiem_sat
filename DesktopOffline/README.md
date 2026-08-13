# Bộ công cụ Kiểm sát Offline

Mô-đun này tạo ứng dụng Windows độc lập dùng WebView2. Mọi mã nguồn hiện có trong
`Tool/` và `Data/` chỉ được đọc và đóng gói; quy trình build không sửa các tệp gốc.

## Nguyên tắc phát hành

- Người dùng tải duy nhất `BoCongCuKiemSat_Offline_Setup.exe`.
- Máy đích không cần Python, pip, Chrome/Edge hoặc Internet.
- Python và thư viện được PyInstaller đóng gói trong thư mục cài đặt.
- WebView2 Fixed Version x64 được nhúng trong bộ cài và dùng riêng cho ứng dụng.
- Tesseract, dữ liệu `vie/eng`, font, CSS và biểu tượng đều nằm trong payload offline.
- Font Be Vietnam Pro Regular/SemiBold/Bold được nhúng cục bộ để hiển thị tiếng Việt ổn định.
- Các công cụ dùng chung logo chuẩn và tông xanh Kiểm sát; chữ ký chỉ xuất hiện tại bảng điều hành tổng.
- Nền hoa sen được tải từ máy chủ cục bộ 127.0.0.1, không sử dụng Internet.
- Chọn thư mục dùng hộp thoại Windows STA riêng, hỗ trợ đường dẫn tiếng Việt và không hiện cửa sổ dòng lệnh.
- Microsoft Word có sẵn trên máy được dùng riêng cho việc chuyển `.doc` cũ sang `.docx`.

## Build

Chạy trên Windows 10/11 x64 có Internet và Python 3.12:

```powershell
powershell -ExecutionPolicy Bypass -File .\DesktopOffline\build.ps1
```

Kết quả cuối cùng nằm tại:

`DesktopOffline/dist/BoCongCuKiemSat_Offline_Setup.exe`

Máy build cần Inno Setup 6. Script dừng với thông báo rõ ràng nếu thiếu runtime hoặc
tài nguyên bắt buộc; không tạo gói phát hành thiếu phụ thuộc.
