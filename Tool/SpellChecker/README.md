# Rà soát chính tả tiếng Việt offline

Ứng dụng rà lỗi trong tệp `.doc` và `.docx`, chạy hoàn toàn trên máy người dùng. Không AI, không API và không gửi tài liệu ra Internet.

## Kiến trúc

- `engine.py`: kiểm tra cụm sai, dấu câu và âm tiết không có trong từ điển; chấp nhận Unicode tổ hợp.
- `docx_processor.py`: duyệt thân bài, bảng, đầu/chân trang; tô vàng vị trí cần kiểm tra hoặc sửa trên bản sao, không tạo Word comment.
- `word_converter.py`: dùng Microsoft Word COM chuyển `.doc` sang `.docx` tạm, không sửa tệp gốc và không chạy macro.
- `app.py`: giao diện Flask chỉ lắng nghe tại `127.0.0.1`.
- `data/vi.dic`: danh sách âm tiết Việt của CSpell, giấy phép MIT.
- `SpellChecker.spec`: đóng gói toàn bộ thành một file EXE bằng PyInstaller.

Không sử dụng Spylls/Hunspell DLL/CSpell runtime vì ứng dụng chỉ cần tập từ và bộ gợi ý được tối ưu riêng. Nhờ vậy không phải đóng gói Node.js, Java hoặc DLL bổ sung.

## Chạy từ mã nguồn

```powershell
python app.py
```

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
python tests\benchmark_engine.py
```

## Build một file EXE

```powershell
python -m PyInstaller --clean --noconfirm SpellChecker.spec
```

Đầu ra: `dist/RaSoatChinhTa.exe`. Máy người dùng không cần cài Python, Flask hay thư viện Python nào khác.

Microsoft Word chỉ bắt buộc khi mở tệp `.doc` định dạng cũ. Tệp `.docx` được xử lý trực tiếp, không cần Microsoft Word. Kết quả luôn được xuất ở định dạng `.docx`.

## Nguyên tắc an toàn

- Không ghi đè tệp gốc.
- Lỗi chắc chắn mới được chọn sửa mặc định.
- Tên riêng, chữ viết tắt và số hiệu được bảo vệ khỏi kiểm tra máy móc.
- Kết quả “nghi vấn” luôn cần người dùng xác nhận.
- Phần mềm hỗ trợ rà soát, không thay thế việc kiểm tra nội dung nghiệp vụ.

## Giấy phép dữ liệu

Danh sách tiếng Việt trong `data/vi.dic` lấy từ `@cspell/dict-vi-vn`, giấy phép MIT. Bản quyền và toàn văn giấy phép nằm tại `data/LICENSE-cspell-vi.txt`.
