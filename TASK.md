# TASK: Gộp 2 Web App Flask (Render) thành Static HTML/CSS/JS (GitHub Pages)

## Thông tin dự án
- **Thư mục gốc:** `d:\Bo_cong_cu_Kiem_sat`
- **Dashboard chính:** `index.html` (ở thư mục gốc)
- **Tài liệu cấu trúc:** `STRUCTURE.md`

---

## CÔNG VIỆC 0 (LÀM TRƯỚC): Đọc file nguồn

Đọc các file sau để hiểu cấu trúc và logic:

1. `Tool/App_tinh_lai_suat/templates/index.html` - Template Flask của App Tính lãi suất
2. `Tool/App_tinh_lai_suat/tinh_lai.py` - Logic Python tính lãi suất (603 dòng)
3. `Tool/App_DS/templates/index.html` - Template Flask của App Tính án phí
4. `Tool/App_DS/app.py` - Logic Python tính án phí (63 dòng)
5. `index.html` (thư mục gốc) - Dashboard chính, tìm mảng TOOLS
6. `STRUCTURE.md` - Tài liệu cấu trúc, tìm mục 3.1 và 3.2

---

## CÔNG VIỆC 1: SỬA `Tool/App_tinh_lai_suat/index.html`

### Bước 1.1: Copy file template
Copy `Tool/App_tinh_lai_suat/templates/index.html` thành `Tool/App_tinh_lai_suat/index.html`

### Bước 1.2: Sửa đường dẫn logo (2 chỗ)
- **Tìm:** `{{ url_for('static', filename='logo_moi.png') }}`
- **Thay bằng:** `static/logo_moi.png`

### Bước 1.3: Thay thế hàm `executeCalculation()`
Trong thẻ `<script>`, tìm hàm `executeCalculation(event)` (bắt đầu từ `function executeCalculation(event)` đến dấu `}` đóng của hàm).

**Thay thế bằng code mới** (xem file `TASK_JS_CODE.md` - Phần REPLACE_EXECUTE_CALCULATION)

### Bước 1.4: Thêm JavaScript tính toán
Ngay trước thẻ `</script>` đóng, chèn toàn bộ code từ file `TASK_JS_CODE.md` - Phần INLINE_JS_FUNCTIONS

---

## CÔNG VIỆC 2: SỬA `Tool/App_DS/index.html`

### Bước 2.1: Copy file template
Copy `Tool/App_DS/templates/index.html` thành `Tool/App_DS/index.html`

### Bước 2.2: Sửa đường dẫn logo
- **Tìm:** `{{ url_for('static', filename='logo_moi.png') }}`
- **Thay bằng:** `static/logo_moi.png`

### Bước 2.3: Sửa form
- **Tìm:** `<form action="/tinh" method="POST">`
- **Thay bằng:** `<form onsubmit="tinhAnPhi(event); return false;">`

### Bước 2.4: Sửa khối hiển thị kết quả (Jinja2)
**Tìm khối:**
```html
{% if gia_tri_nhap %}
<div class="receipt">
    <h4 style="color: #0056b3;">Biên lai tính phí chi tiết</h4>
    <p><strong>Giá trị tranh chấp:</strong> {{ "{:,.0f}".format(gia_tri_nhap) }} VNĐ</p>
    <p><strong>Công thức áp dụng:</strong> {{ cong_thuc }}</p>
    <hr>
    <h3 style="color: #d9534f;">Tổng án phí: {{ ket_qua }} VNĐ</h3>
    <p style="font-size: 0.8em; color: #666;">* Áp dụng theo Nghị quyết 326/2016/UBTVQH14</p>
</div>
{% endif %}
```

**Thay bằng:**
```html
<div class="receipt" id="receiptResult" style="display: none;">
    <h4 style="color: #0056b3;">Biên lai tính phí chi tiết</h4>
    <p><strong>Giá trị tranh chấp:</strong> <span id="receiptGiaTri"></span> VNĐ</p>
    <p><strong>Công thức áp dụng:</strong> <span id="receiptCongThuc"></span></p>
    <hr>
    <h3 style="color: #d9534f;">Tổng án phí: <span id="receiptKetQua"></span> VNĐ</h3>
    <p style="font-size: 0.8em; color: #666;">* Áp dụng theo Nghị quyết 326/2016/UBTVQH14</p>
</div>
```

### Bước 2.5: Thêm JavaScript tính toán
Thêm vào cuối file (trước `</body>` hoặc trong thẻ `<script>` cuối cùng):

```html
<script>
function tinhAnPhi(event) {
    event.preventDefault();
    const loai_phi = document.querySelector('select[name="loai_phi"]').value;
    const gia_tri = parseFloat(document.querySelector('input[name="gia_tri"]').value) || 0;
    let ket_qua = 0, cong_thuc = "";
    
    if (loai_phi === 'lao_dong_co_gia_ngach') {
        if (gia_tri <= 6000000) { ket_qua = 300000; cong_thuc = "Mức cố định: 300.000 VNĐ"; }
        else if (gia_tri <= 400000000) { ket_qua = gia_tri * 0.03; cong_thuc = gia_tri.toLocaleString('vi-VN') + " x 3% (tối thiểu 300k)"; }
        else if (gia_tri <= 2000000000) { ket_qua = 12000000 + (gia_tri - 400000000) * 0.02; cong_thuc = "12tr + (" + gia_tri.toLocaleString('vi-VN') + " - 400tr) x 2%"; }
        else { ket_qua = 44000000 + (gia_tri - 2000000000) * 0.001; cong_thuc = "44tr + (" + gia_tri.toLocaleString('vi-VN') + " - 2 tỷ) x 0.1%"; }
        ket_qua = Math.max(300000, ket_qua);
    } else {
        if (gia_tri <= 6000000) { ket_qua = 300000; cong_thuc = "Mức cố định: 300.000 VNĐ"; }
        else if (gia_tri <= 400000000) { ket_qua = gia_tri * 0.05; cong_thuc = gia_tri.toLocaleString('vi-VN') + " x 5%"; }
        else if (gia_tri <= 800000000) { ket_qua = 20000000 + (gia_tri - 400000000) * 0.04; cong_thuc = "20tr + (" + gia_tri.toLocaleString('vi-VN') + " - 400tr) x 4%"; }
        else if (gia_tri <= 2000000000) { ket_qua = 36000000 + (gia_tri - 800000000) * 0.03; cong_thuc = "36tr + (" + gia_tri.toLocaleString('vi-VN') + " - 800tr) x 3%"; }
        else if (gia_tri <= 4000000000) { ket_qua = 72000000 + (gia_tri - 2000000000) * 0.02; cong_thuc = "72tr + (" + gia_tri.toLocaleString('vi-VN') + " - 2 tỷ) x 2%"; }
        else { ket_qua = 112000000 + (gia_tri - 4000000000) * 0.001; cong_thuc = "112tr + (" + gia_tri.toLocaleString('vi-VN') + " - 4 tỷ) x 0.1%"; }
    }
    document.getElementById('receiptGiaTri').innerText = gia_tri.toLocaleString('vi-VN');
    document.getElementById('receiptCongThuc').innerText = cong_thuc;
    document.getElementById('receiptKetQua').innerText = Math.round(ket_qua).toLocaleString('vi-VN');
    document.getElementById('receiptResult').style.display = 'block';
}
</script>
```

---

## CÔNG VIỆC 3: CẬP NHẬT DASHBOARD `index.html`

Mở `index.html` (thư mục gốc), tìm mảng `TOOLS` và sửa 2 dòng:

### Bước 3.1: Sửa URL "Tính lãi suất"
**Tìm:** `url:'https://app-tinh-lai-suat.onrender.com/'`
**Thay:** `url:'Tool/App_tinh_lai_suat/index.html'`

### Bước 3.2: Sửa URL "Tính án phí"
**Tìm:** `url:'https://an-phi-kiem-sat.onrender.com'`
**Thay:** `url:'Tool/App_DS/index.html'`

---

## CÔNG VIỆC 4: CẬP NHẬT `STRUCTURE.md`

### Bước 4.1: Sửa mục 3.1 (Tính lãi suất)
**Tìm:** `| **Loại** | Web app external (iframe) |`
**Thay:** `| **Loại** | Static HTML (iframe) |`

**Tìm:** `| **URL** | \`https://app-tinh-lai-suat.onrender.com/\` |`
**Thay:** `| **URL** | \`Tool/App_tinh_lai_suat/index.html\` |`

### Bước 4.2: Sửa mục 3.2 (Tính án phí)
**Tìm:** `| **Loại** | Web app external (iframe) |`
**Thay:** `| **Loại** | Static HTML (iframe) |`

**Tìm:** `| **URL** | \`https://an-phi-kiem-sat.onrender.com\` |`
**Thay:** `| **URL** | \`Tool/App_DS/index.html\` |`

---

## KIỂM TRA SAU KHI HOÀN THÀNH

1. Mở `Tool/App_tinh_lai_suat/index.html` trong trình duyệt - kiểm tra form tính lãi hoạt động
2. Mở `Tool/App_DS/index.html` trong trình duyệt - kiểm tra form tính án phí hoạt động
3. Mở `index.html` (gốc) - kiểm tra 2 tool mở được trong iframe
4. Xóa file tạm: `TASK.json`, `TASK.md`, `TASK_JS_CODE.md` (nếu có)
