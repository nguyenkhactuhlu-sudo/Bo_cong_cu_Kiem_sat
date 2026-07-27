# TASK: SỬA TOOL TÍNH THỜI HẠN TẠM GIỮ, TẠM GIAM

**File cần sửa:** `Data/TinhTuoiThoiHan.html`
**Ngày:** 27/07/2026

---

## MỤC TIÊU

Tool sau khi sửa sẽ có **3 phần riêng biệt**:

| # | Phần | Đơn vị | Rules ngày nghỉ | Căn cứ pháp lý |
|---|------|--------|-----------------|----------------|
| 1 | Tạm giữ | Giờ | N/A | Điều 117, 118 BLTTHS |
| 2 | **Tạm giam (MỚI)** | Tháng + Ngày | Không dời (tính liên tục cả ngày nghỉ) | Điều 17 TT 04/2018 |
| 3 | Thời hạn tố tụng | Năm+Tháng+Ngày | **Có dời** sang ngày làm việc | Điều 134, 135 BLTTHS |

---

## CĂN CỨ PHÁP LÝ PHẦN TẠM GIAM (trích nguyên văn)

**Điều 17 Thông tư liên tịch số 04/2018/TTLT-VKSNDTC-BCA-BQP** ngày 19 tháng 10 năm 2018
quy định về phối hợp giữa Cơ quan điều tra và Viện kiểm sát trong việc thực hiện
một số quy định của Bộ luật Tố tụng hình sự:

> 1. Thời hạn tạm giữ được trừ vào thời hạn tạm giam để điều tra. Nếu việc tạm giam
>    liên tục với việc tạm giữ thì thời hạn tạm giam được tính tiếp từ ngày hết thời
>    hạn tạm giữ. Nếu việc tạm giam không liên tục với việc tạm giữ thì thời hạn tạm
>    giam được tính kể từ ngày bắt bị can để tạm giam cho đến ngày kết thúc được ghi
>    trong lệnh (đã trừ đi số ngày bị tạm giữ). Thời điểm cuối cùng của thời hạn tạm
>    giam là 24 giờ 00 phút của ngày cuối cùng được ghi trong lệnh. Khi tính thời hạn
>    tạm giữ, tạm giam phải căn cứ vào thời hạn thực tế được ghi trong quyết định tạm
>    giữ, lệnh tạm giam, lệnh bắt bị can để tạm giam và tính liên tục cả ngày nghỉ
>    (thứ bảy, chủ nhật, ngày lễ, ngày tết), **01 tháng tạm giam được tính bằng 30 ngày**.
>
> 2. Cách ghi thời hạn trong lệnh tạm giam, lệnh bắt bị can để tạm giam trong trường
>    hợp trước đó bị can đã bị tạm giữ được thực hiện như sau: thời hạn tạm giam được
>    tính theo ngày, bắt đầu kể từ ngày cuối cùng của thời hạn tạm giữ hoặc ngày bắt
>    bị can để tạm giam và kết thúc vào ngày cuối cùng của thời hạn tạm giam (sau khi
>    đã trừ đi số ngày tạm giữ).

**Ví dụ 1 (liên tục):** Nguyễn Văn A bị tạm giữ 03 ngày, từ 10 giờ 00 phút ngày 01/3/2025
đến 10 giờ 00 phút ngày 04/3/2025, sau đó A bị khởi tố bị can và bị ra lệnh tạm giam
02 tháng, thì thời hạn tạm giam thực tế đối với bị can là **01 tháng 27 ngày** (đã trừ
03 ngày tạm giữ). Hết hạn: **ngày 29/4/2025**.

**Ví dụ 2 (không liên tục):** Trần Thị B bị tạm giữ 06 ngày, từ 14 giờ 00 phút ngày
05/3/2025 đến 14 giờ 00 phút ngày 11/3/2025 thì được áp dụng biện pháp cấm đi khỏi
nơi cư trú. Đến ngày 11/4/2025 bị can B bị bắt để tạm giam thời hạn là 02 tháng, thì
thời hạn tạm giam đối với bị can B là **01 tháng 24 ngày** (đã trừ 06 ngày tạm giữ).
Hết hạn: **ngày 03/6/2025**.

---

## CÔNG VIỆC CHI TIẾT

### A. SỬA LOGIC PHẦN "THỜI HẠN TỐ TỤNG" (Phần 3)

#### A1. Xóa đoạn `adjustedStartDate` (dòng ~1227-1242 trong file hiện tại)
- **Vị trí:** Trong hàm `calculate()`, ngay trước dòng `var result = { year: adjustedStartYear, month: adjustedStartMonth, day: adjustedStartDay };`
- **Hiện tại:** Code tạo `adjustedDate` bằng cách cộng +1 ngày vào `startDate`
- **Hành động:** XÓA TOÀN BỘ block `if (durDay > 0 || durMonth > 0 || durYear > 0) { ... adjustedDate ... }` (khoảng 15 dòng)
- **Code mới thay vào chỗ đó:**
  ```javascript
  // Dùng trực tiếp ngày bắt đầu làm mốc (không +1 ngày)
  var result = { year: startYear, month: startMonth, day: startDay };
  ```

#### A2. Giữ nguyên các hàm khác
- `calculateDate()` → giữ nguyên (tính theo lịch thực tế)
- `isHolidayOrWeekend()`, `getNextWorkingDay()` → giữ nguyên (dời ngày nghỉ)
- `displayResult()` → giữ nguyên

#### A3. Sửa comment trong code (dòng 1199-1201)
- Sửa comment `// TÍNH TOÁN CHÍNH (ĐÃ SỬA LỖI LỆCH NGÀY - Điều 135 BLTTHS)`
- Thành: `// TÍNH TOÁN CHÍNH (Tính từ mốc gốc, không +1 ngày)`

---

### B. THÊM MỚI PHẦN "TẠM GIAM" (Phần 2, chèn giữa Tạm giữ và Thời hạn)

#### Vị trí chèn
Chèn vào giữa dòng kết thúc `</fieldset>` của phần Tạm giữ (sau dòng ~926)
và dòng mở đầu `<!-- PHẦN 2: TÍNH TUỔI & TÍNH THỜI HẠN (Điều 135 BLTTHS) -->`
của phần Thời hạn (trước dòng ~928).

#### B1. Thêm CSS (chèn vào block `<style>` gần cuối, trước `</style>`)

Thêm toàn bộ block sau:

```css
/* ============ TẠM GIAM STYLES ============ */
.fieldset-tamgiam {
    border-color: var(--green-dark) !important;
}
.fieldset-tamgiam legend {
    background: linear-gradient(135deg, #0d5e3a, #1a8a54);
    border: 1px solid var(--green-light);
    color: #fff;
}
.legal-note-tamgiam {
    background: rgba(26, 122, 76, 0.07);
    border: 1px solid rgba(26, 122, 76, 0.2);
    color: #0d5e3a;
}
.legal-note-tamgiam i {
    color: var(--green-dark);
}
.btn-tamgiam {
    background: linear-gradient(135deg, #0d5e3a, #1a8a54) !important;
    box-shadow: 0 4px 16px rgba(26, 122, 76, 0.3) !important;
}
.btn-tamgiam:hover {
    box-shadow: 0 8px 24px rgba(26, 122, 76, 0.4) !important;
}
.tamgiam-result {
    margin-top: 20px;
}
.tamgiam-result-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 14px;
    margin-bottom: 16px;
}
.tamgiam-result-item {
    background: #fff;
    border-radius: 12px;
    padding: 16px 14px;
    text-align: center;
    border: 1px solid rgba(26, 122, 76, 0.15);
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.tamgiam-result-item .label {
    font-size: 11px;
    font-weight: 700;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}
.tamgiam-result-item .value {
    font-size: 24px;
    font-weight: 800;
    color: var(--green-dark);
}
.tamgiam-result-item .sub {
    font-size: 13px;
    font-weight: 600;
    color: #666;
    margin-top: 4px;
}
.tamgiam-result-item .sub-small {
    font-size: 11px;
    color: #999;
    margin-top: 2px;
}
.tamgiam-warning {
    padding: 14px 18px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 15px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-bottom: 14px;
    animation: fadeIn 0.5s ease-out;
}
.tamgiam-warning i { font-size: 20px; }
.tamgiam-warning.danger {
    background: rgba(220, 38, 38, 0.1);
    border: 2px solid var(--red-warning);
    color: var(--red-warning);
}
.tamgiam-warning.caution {
    background: rgba(217, 119, 6, 0.1);
    border: 2px solid var(--yellow-warning);
    color: var(--yellow-warning);
}
.tamgiam-warning.safe {
    background: rgba(26, 122, 76, 0.08);
    border: 2px solid var(--green-dark);
    color: var(--green-dark);
}
#tgiam-result-section .result-card {
    border-color: var(--green-light) !important;
}
```

#### B2. Thêm HTML fieldset Tạm giam

Chèn toàn bộ đoạn HTML sau vào vị trí giữa fieldset Tạm giữ và fieldset Thời hạn:

```html
<!-- ============================================================ -->
<!-- PHẦN 2: TÍNH THỜI HẠN TẠM GIAM (Điều 17 TT 04/2018) -->
<!-- ============================================================ -->
<div class="fieldset-section">
    <fieldset class="fieldset-tamgiam">
        <legend><i class="fa-solid fa-gavel"></i> TÍNH THỜI HẠN TẠM GIAM</legend>

        <div class="form-section">
            <!-- CỘT TRÁI: Ngày bắt đầu -->
            <div class="form-card">
                <div class="card-title" style="color:var(--green-dark);border-bottom-color:var(--green-light);">
                    <i class="fa-solid fa-play-circle"></i>
                    Ngày bắt đầu tạm giam
                </div>

                <div class="form-group">
                    <label>Ngày - Tháng - Năm</label>
                    <div class="form-row-3">
                        <div><input type="number" id="tgiam-day" min="1" max="31" placeholder="Ngày" value="1"></div>
                        <div><input type="number" id="tgiam-month" min="1" max="12" placeholder="Tháng" value="1"></div>
                        <div><input type="number" id="tgiam-year" min="1" max="9999" placeholder="Năm" value="2026"></div>
                    </div>
                </div>

                <div class="form-group">
                    <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
                        <input type="checkbox" id="tgiam-lientuc" onchange="toggleTamGiamContinuous()" style="width:18px;height:18px;cursor:pointer;">
                        Tạm giam liên tục với tạm giữ (tự động lấy ngày hết hạn tạm giữ làm ngày bắt đầu)
                    </label>
                </div>

                <div class="form-group" id="tgiam-ngaybatdau-group">
                    <label>Số ngày đã tạm giữ (để trừ vào thời hạn tạm giam)</label>
                    <div style="display:flex;align-items:center;gap:10px;">
                        <input type="number" id="tgiam-da-tamgiu" min="0" placeholder="0" value="0" style="flex:1;">
                        <span style="font-size:13px;font-weight:600;color:#666;">ngày</span>
                    </div>
                </div>

                <div style="margin-top:8px;text-align:right;">
                    <button onclick="fillCurrentTimeTGIAM()" style="padding:6px 14px;border:1px solid rgba(26,122,76,0.25);border-radius:8px;background:transparent;font-family:inherit;font-size:12px;font-weight:600;color:var(--green-dark);cursor:pointer;">
                        <i class="fa-regular fa-clock"></i> Lấy ngày hiện tại
                    </button>
                </div>
            </div>

            <!-- CỘT PHẢI: Thời hạn tạm giam -->
            <div class="form-card">
                <div class="card-title" style="color:var(--green-dark);border-bottom-color:var(--green-light);">
                    <i class="fa-solid fa-hourglass-half"></i>
                    Thời hạn tạm giam (ghi trong lệnh)
                </div>

                <div class="form-group">
                    <label>Thời hạn gốc</label>
                    <div class="form-row">
                        <div>
                            <label style="font-size:11px;color:#999;font-weight:600;">Tháng</label>
                            <input type="number" id="tgiam-thang" min="0" placeholder="0" value="0">
                        </div>
                        <div>
                            <label style="font-size:11px;color:#999;font-weight:600;">Ngày</label>
                            <input type="number" id="tgiam-ngay" min="0" placeholder="0" value="0">
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label>Ví dụ nhanh</label>
                    <div style="display:flex;flex-wrap:wrap;gap:6px;">
                        <button class="quick-example" style="border-color:rgba(26,122,76,0.25);background:rgba(26,122,76,0.06);color:var(--green-dark);" onclick="quickExampleTGiam(1,0)">1 tháng</button>
                        <button class="quick-example" style="border-color:rgba(26,122,76,0.25);background:rgba(26,122,76,0.06);color:var(--green-dark);" onclick="quickExampleTGiam(2,0)">2 tháng</button>
                        <button class="quick-example" style="border-color:rgba(26,122,76,0.25);background:rgba(26,122,76,0.06);color:var(--green-dark);" onclick="quickExampleTGiam(3,0)">3 tháng</button>
                        <button class="quick-example" style="border-color:rgba(26,122,76,0.25);background:rgba(26,122,76,0.06);color:var(--green-dark);" onclick="quickExampleTGiam(4,0)">4 tháng</button>
                    </div>
                </div>

                <button class="btn-calculate btn-tamgiam" onclick="calculateTamGiam()">
                    <i class="fa-solid fa-calculator"></i> TÍNH THỜI HẠN TẠM GIAM
                </button>
            </div>
        </div>

        <!-- Kết quả tạm giam -->
        <div class="result-section" id="tgiam-result-section">
            <div class="result-card" style="margin-top:20px;border-color:var(--green-light)!important;">
                <div class="result-header">
                    <h2 style="color:var(--green-dark);"><i class="fa-solid fa-check-circle"></i> KẾT QUẢ THỜI HẠN TẠM GIAM</h2>
                </div>
                <div id="tgiam-result-content"></div>
            </div>
        </div>

        <!-- Ghi chú pháp lý Điều 17 TT 04/2018 -->
        <div class="legal-note legal-note-tamgiam" style="max-height: 450px; overflow-y: auto; font-size: 13px; line-height: 1.7;">
            <i class="fa-solid fa-scale-balanced" style="margin-top: 2px;"></i>
            <div>
                <strong style="font-size: 15px; display: block; margin-bottom: 8px;">Căn cứ pháp lý</strong>

                <p><strong>Điều 17 Thông tư liên tịch số 04/2018/TTLT-VKSNDTC-BCA-BQP</strong> ngày 19 tháng 10 năm 2018 quy định về phối hợp giữa Cơ quan điều tra và Viện kiểm sát trong việc thực hiện một số quy định của Bộ luật Tố tụng hình sự:</p>

                <p><strong>Tính thời hạn tạm giam trong trường hợp bị can đã bị tạm giữ và cách ghi thời hạn trong lệnh tạm giam, lệnh bắt bị can để tạm giam đối với bị can đã bị tạm giữ</strong></p>

                <p>1. Thời hạn tạm giữ được trừ vào thời hạn tạm giam để điều tra. Nếu việc tạm giam liên tục với việc tạm giữ thì thời hạn tạm giam được tính tiếp từ ngày hết thời hạn tạm giữ. Nếu việc tạm giam không liên tục với việc tạm giữ thì thời hạn tạm giam được tính kể từ ngày bắt bị can để tạm giam cho đến ngày kết thúc được ghi trong lệnh (đã trừ đi số ngày bị tạm giữ). Thời điểm cuối cùng của thời hạn tạm giam là 24 giờ 00 phút của ngày cuối cùng được ghi trong lệnh. Khi tính thời hạn tạm giữ, tạm giam phải căn cứ vào thời hạn thực tế được ghi trong quyết định tạm giữ, lệnh tạm giam, lệnh bắt bị can để tạm giam và <strong>tính liên tục cả ngày nghỉ (thứ bảy, chủ nhật, ngày lễ, ngày tết), 01 tháng tạm giam được tính bằng 30 ngày</strong>.</p>

                <p>2. Cách ghi thời hạn trong lệnh tạm giam, lệnh bắt bị can để tạm giam trong trường hợp trước đó bị can đã bị tạm giữ được thực hiện như sau: thời hạn tạm giam được tính theo ngày, bắt đầu kể từ ngày cuối cùng của thời hạn tạm giữ hoặc ngày bắt bị can để tạm giam và kết thúc vào ngày cuối cùng của thời hạn tạm giam (sau khi đã trừ đi số ngày tạm giữ).</p>

                <p style="margin-top: 10px; padding: 10px; background: rgba(26,122,76,0.06); border-radius: 8px; border-left: 3px solid var(--green-dark);">
                    <strong>Ví dụ 1:</strong> Nguyễn Văn A bị tạm giữ 03 ngày, từ 10 giờ 00 phút ngày 01/3/2025 đến 10 giờ 00 phút ngày 04/3/2025, sau đó A bị khởi tố bị can và bị ra lệnh tạm giam 02 tháng, thì thời hạn tạm giam thực tế đối với bị can là 01 tháng 27 ngày (đã trừ 03 ngày tạm giữ). Do đó, thời hạn trong lệnh tạm giam ghi là: tạm giam trong thời hạn 01 tháng 27 ngày, kể từ ngày 04/3/2025 đến hết ngày 29/4/2025.
                </p>

                <p style="padding: 10px; background: rgba(26,122,76,0.06); border-radius: 8px; border-left: 3px solid var(--green-dark);">
                    <strong>Ví dụ 2:</strong> Trần Thị B bị tạm giữ 06 ngày, từ 14 giờ 00 phút ngày 05/3/2025 đến 14 giờ 00 phút ngày 11/3/2025 thì được áp dụng biện pháp cấm đi khỏi nơi cư trú. Đến ngày 11/4/2025 bị can B bị bắt để tạm giam thời hạn là 02 tháng, thì thời hạn tạm giam đối với bị can B là 01 tháng 24 ngày (đã trừ 06 ngày tạm giữ). Do đó, thời hạn trong lệnh bắt bị can để tạm giam ghi là: tạm giam trong thời hạn 01 tháng 24 ngày, kể từ ngày 11/4/2025 đến hết ngày 03/6/2025.
                </p>
            </div>
        </div>
    </fieldset>
</div>
```

#### B3. Thêm JavaScript cho Tạm giam

Chèn vào cuối block `<script>`, ngay trước `</script>` (dòng ~1652):

```javascript
// ============================================================
// CHỨC NĂNG TÍNH TẠM GIAM (Điều 17 TT 04/2018)
// ============================================================

function toggleTamGiamContinuous() {
    var isContinuous = document.getElementById('tgiam-lientuc').checked;
    var ngayBatDauGroup = document.getElementById('tgiam-ngaybatdau-group');
    ngayBatDauGroup.style.display = 'block';
    // Nếu lấy ngày hết hạn từ phần tạm giữ, user có thể copy thủ công
}

function fillCurrentTimeTGIAM() {
    var now = new Date();
    document.getElementById('tgiam-day').value = now.getDate();
    document.getElementById('tgiam-month').value = now.getMonth() + 1;
    document.getElementById('tgiam-year').value = now.getFullYear();
}

function quickExampleTGiam(thang, ngay) {
    document.getElementById('tgiam-thang').value = thang;
    document.getElementById('tgiam-ngay').value = ngay;
    calculateTamGiam();
}

function calculateTamGiam() {
    // Đọc dữ liệu đầu vào
    var startDay = parseInt(document.getElementById('tgiam-day').value) || 1;
    var startMonth = parseInt(document.getElementById('tgiam-month').value) || 1;
    var startYear = parseInt(document.getElementById('tgiam-year').value) || 2026;

    var thangGoc = parseInt(document.getElementById('tgiam-thang').value) || 0;
    var ngayGoc = parseInt(document.getElementById('tgiam-ngay').value) || 0;
    var daTamGiu = parseInt(document.getElementById('tgiam-da-tamgiu').value) || 0;

    // Validate
    if (thangGoc === 0 && ngayGoc === 0) {
        alert('Vui lòng nhập thời hạn tạm giam (tháng hoặc ngày).');
        return;
    }

    if (!isValidDate(startYear, startMonth, startDay)) {
        alert('Ngày tháng không hợp lệ! Vui lòng kiểm tra lại.');
        return;
    }

    // === LOGIC THEO ĐIỀU 17 TT 04/2018 ===
    // 1. 1 tháng = 30 ngày (cố định)
    var tongNgayGoc = thangGoc * 30 + ngayGoc;

    // 2. Trừ số ngày đã tạm giữ
    var tongNgayThucTe = tongNgayGoc - daTamGiu;
    if (tongNgayThucTe <= 0) {
        alert('Thời hạn tạm giam thực tế không hợp lệ (≤ 0 ngày). Vui lòng kiểm tra số ngày đã tạm giữ.');
        return;
    }

    // 3. Quy đổi ngược ra tháng + ngày để hiển thị
    var thangThucTe = Math.floor(tongNgayThucTe / 30);
    var ngayThucTe = tongNgayThucTe % 30;

    // 4. Tính ngày hết hạn
    //    "Kể từ ngày X" → ngày X là ngày thứ 1
    //    → endDate = startDate + (tổng_ngày_thực_tế - 1)
    var startDate = new Date(startYear, startMonth - 1, startDay);
    var endDate = new Date(startDate);
    endDate.setDate(endDate.getDate() + tongNgayThucTe - 1);

    // 5. KHÔNG dời ngày nghỉ (tính liên tục cả T7, CN, Lễ, Tết)

    // 6. Tính thời gian đã qua / còn lại (so với hiện tại)
    var now = new Date();
    // Tính elapsed: số ngày đã qua từ startDate đến now
    var elapsedDays = Math.floor((now.getTime() - startDate.getTime()) / (24 * 60 * 60 * 1000));
    // Nếu chưa đến startDate thì elapsed = 0
    if (elapsedDays < 0) elapsedDays = 0;
    // Tính remaining: số ngày còn lại từ hôm nay đến endDate (tính luôn hôm nay nếu chưa quá)
    var remainingDays = Math.floor((endDate.getTime() - now.getTime()) / (24 * 60 * 60 * 1000)) + 1;
    if (remainingDays < 0) remainingDays = 0;

    // Hiển thị
    displayTamGiamResult(startDate, endDate, thangGoc, ngayGoc, daTamGiu, thangThucTe, ngayThucTe, tongNgayThucTe, elapsedDays, remainingDays);
}

function displayTamGiamResult(startDate, endDate, thangGoc, ngayGoc, daTamGiu, thangThucTe, ngayThucTe, tongNgayThucTe, elapsedDays, remainingDays) {
    var section = document.getElementById('tgiam-result-section');
    section.classList.add('visible');
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });

    var content = document.getElementById('tgiam-result-content');
    var dayNames = ['Chủ nhật', 'Thứ hai', 'Thứ ba', 'Thứ tư', 'Thứ năm', 'Thứ sáu', 'Thứ bảy'];

    // Warning banner
    var warningHtml = '';
    if (remainingDays <= 0) {
        warningHtml += '<div class="tamgiam-warning danger">';
        warningHtml += '<i class="fa-solid fa-circle-exclamation"></i>';
        warningHtml += '<span>ĐÃ HẾT HẠN TẠM GIAM! Thời hạn tạm giam đã kết thúc.</span>';
        warningHtml += '</div>';
    } else if (remainingDays <= 3) {
        warningHtml += '<div class="tamgiam-warning danger">';
        warningHtml += '<i class="fa-solid fa-circle-exclamation"></i>';
        warningHtml += '<span>CẢNH BÁO: Thời gian tạm giam sắp hết! Còn ' + remainingDays + ' ngày.</span>';
        warningHtml += '</div>';
    } else if (remainingDays <= 10) {
        warningHtml += '<div class="tamgiam-warning caution">';
        warningHtml += '<i class="fa-solid fa-triangle-exclamation"></i>';
        warningHtml += '<span>Lưu ý: Thời gian tạm giam còn dưới 10 ngày. Còn ' + remainingDays + ' ngày.</span>';
        warningHtml += '</div>';
    } else {
        warningHtml += '<div class="tamgiam-warning safe">';
        warningHtml += '<i class="fa-solid fa-check-circle"></i>';
        warningHtml += '<span>Thời gian tạm giam còn ' + remainingDays + ' ngày.</span>';
        warningHtml += '</div>';
    }

    // Result grid
    var gridHtml = '<div class="tamgiam-result-grid">';

    gridHtml += '<div class="tamgiam-result-item">';
    gridHtml += '<div class="label">Bắt đầu</div>';
    gridHtml += '<div class="value time-value">' + pad(startDate.getDate()) + '/' + pad(startDate.getMonth() + 1) + '/' + startDate.getFullYear() + '</div>';
    gridHtml += '<div class="sub-small">' + dayNames[startDate.getDay()] + '</div>';
    gridHtml += '</div>';

    gridHtml += '<div class="tamgiam-result-item">';
    gridHtml += '<div class="label">Hết hạn (24h00)</div>';
    gridHtml += '<div class="value time-value" style="color:var(--bronze);">' + pad(endDate.getDate()) + '/' + pad(endDate.getMonth() + 1) + '/' + endDate.getFullYear() + '</div>';
    gridHtml += '<div class="sub-small">' + dayNames[endDate.getDay()] + '</div>';
    gridHtml += '</div>';

    gridHtml += '<div class="tamgiam-result-item">';
    gridHtml += '<div class="label">Thời hạn gốc</div>';
    var gocStr = '';
    if (thangGoc > 0) gocStr += thangGoc + ' tháng';
    if (ngayGoc > 0) gocStr += (gocStr ? ' ' : '') + ngayGoc + ' ngày';
    gridHtml += '<div class="value" style="font-size:20px;">' + gocStr + '</div>';
    gridHtml += '<div class="sub">= ' + (thangGoc * 30 + ngayGoc) + ' ngày</div>';
    gridHtml += '</div>';

    gridHtml += '<div class="tamgiam-result-item">';
    gridHtml += '<div class="label">Thời hạn thực tế</div>';
    var ttStr = '';
    if (thangThucTe > 0) ttStr += thangThucTe + ' tháng';
    if (ngayThucTe > 0) ttStr += (ttStr ? ' ' : '') + ngayThucTe + ' ngày';
    if (ttStr === '') ttStr = '0 ngày';
    gridHtml += '<div class="value" style="font-size:20px;">' + ttStr + '</div>';
    gridHtml += '<div class="sub">= ' + tongNgayThucTe + ' ngày (đã trừ ' + daTamGiu + ' ngày tạm giữ)</div>';
    gridHtml += '</div>';

    // Đã qua
    var elapsedClass = 'normal';
    if (elapsedDays >= tongNgayThucTe) elapsedClass = 'warning-red';
    else if (elapsedDays >= tongNgayThucTe * 0.75) elapsedClass = 'warning-yellow';
    gridHtml += '<div class="tamgiam-result-item">';
    gridHtml += '<div class="label">Đã qua</div>';
    gridHtml += '<div class="value ' + elapsedClass + '" style="font-size:22px;">' + (elapsedDays > 0 ? elapsedDays : 0) + '</div>';
    gridHtml += '<div class="sub">ngày (' + Math.min(100, Math.round(elapsedDays / tongNgayThucTe * 100)) + '%)</div>';
    gridHtml += '</div>';

    // Còn lại
    var remClass = 'normal';
    if (remainingDays <= 0) remClass = 'warning-red';
    else if (remainingDays <= 3) remClass = 'warning-red';
    else if (remainingDays <= 10) remClass = 'warning-yellow';
    gridHtml += '<div class="tamgiam-result-item">';
    gridHtml += '<div class="label">Còn lại</div>';
    gridHtml += '<div class="value ' + remClass + '" style="font-size:22px;">' + (remainingDays > 0 ? remainingDays : 'HẾT') + '</div>';
    gridHtml += '<div class="sub">' + (remainingDays > 0 ? 'ngày (' + Math.round(remainingDays / tongNgayThucTe * 100) + '%)' : '') + '</div>';
    gridHtml += '</div>';

    gridHtml += '</div>'; // close tamgiam-result-grid

    // Summary
    var summaryHtml = '<div class="result-summary">';
    summaryHtml += '<p>';
    summaryHtml += 'Tạm giam từ <span class="big-date">' + pad(startDate.getDate()) + '/' + pad(startDate.getMonth() + 1) + '/' + startDate.getFullYear() + '</span>';
    summaryHtml += ' <span class="arrow-icon">→</span> ';
    summaryHtml += 'Hết hạn lúc <strong style="color:var(--bronze);font-size:18px;">24h00 ngày ' + pad(endDate.getDate()) + '/' + pad(endDate.getMonth() + 1) + '/' + endDate.getFullYear() + '</strong>';
    summaryHtml += '</p>';
    summaryHtml += '<p style="margin-top:8px;font-size:14px;color:#666;">';
    summaryHtml += 'Thời hạn thực tế: <strong>' + tongNgayThucTe + ' ngày</strong>';
    if (daTamGiu > 0) summaryHtml += ' (đã trừ ' + daTamGiu + ' ngày tạm giữ)';
    summaryHtml += ' &middot; 1 tháng = 30 ngày';
    summaryHtml += ' &middot; Tính liên tục cả ngày nghỉ';
    summaryHtml += '</p>';
    summaryHtml += '</div>';

    content.innerHTML = warningHtml + summaryHtml + gridHtml;
}
```

---

### C. SỬA COMMENT (dòng 1199-1201)

| Cũ | Mới |
|----|-----|
| `// TÍNH TOÁN CHÍNH (ĐÃ SỬA LỖI LỆCH NGÀY - Điều 135 BLTTHS)` | `// TÍNH TOÁN CHÍNH (Tính từ mốc gốc, không +1 ngày)` |

---

### D. KIỂM THỬ (Test cases)

| # | Test case | Phần | Input | Kết quả mong đợi |
|---|-----------|------|-------|------------------|
| 1 | Ví dụ 1 (TT 04/2018) | Tạm giam | Start: 04/3/2025, TG: 2th0ng, Tạm giữ: 3 ngày | Hết hạn: **29/4/2025** |
| 2 | Ví dụ 2 (TT 04/2018) | Tạm giam | Start: 11/4/2025, TG: 2th0ng, Tạm giữ: 6 ngày | Hết hạn: **03/6/2025** |
| 3 | Không có tạm giữ | Tạm giam | Start: 01/7/2026, TG: 2th0ng, Tạm giữ: 0 | Hết hạn: **30/8/2026** (60 ngày) |
| 4 | Ngày nghỉ (không dời) | Tạm giam | Start: 01/7/2026 (T4), TG: 0th5ng | Hết hạn: **05/7/2026 (CN)** → không dời |
| 5 | +1 ngày (đã sửa) | Thời hạn | Start: 01/7/2026, +1 ngày | **02/7/2026** (không +1 ngày) |
| 6 | Ngày nghỉ (có dời) | Thời hạn | Start: 01/7/2026 (T4), +4 ngày → 05/7 (CN) | Cảnh báo dời sang **06/7 (T2)** |

---

## TÓM TẮT CÁC BƯỚC

1. [ ] **A1**: Trong hàm `calculate()`, xóa block `adjustedStartDate` (15 dòng), thay bằng `var result = { year: startYear, month: startMonth, day: startDay };`
2. [ ] **A3**: Sửa comment dòng 1199-1201
3. [ ] **B1**: Thêm CSS cho phần Tạm giam vào cuối block `<style>`
4. [ ] **B2**: Thêm HTML fieldset Tạm giam vào giữa fieldset Tạm giữ và fieldset Thời hạn
5. [ ] **B3**: Thêm 5 hàm JavaScript (`toggleTamGiamContinuous`, `fillCurrentTimeTGIAM`, `quickExampleTGiam`, `calculateTamGiam`, `displayTamGiamResult`) vào cuối block `<script>`
6. [ ] **D**: Kiểm thử 6 test case