# JavaScript code for Tool/App_tinh_lai_suat/index.html

## Phần 1: REPLACE_EXECUTE_CALCULATION

Thay thế toàn bộ hàm `executeCalculation(event)` hiện có bằng code dưới đây:

```javascript
function executeCalculation(event) {
    event.preventDefault();

    const list_tha_noi = [];
    document.querySelectorAll('.floating-row').forEach(row => {
        if(row.querySelector('.tn-rate').value) {
            list_tha_noi.push({
                rate: row.querySelector('.tn-rate').value,
                unit: row.querySelector('.tn-unit').value,
                from: row.querySelector('.tn-from').value,
                to: row.querySelector('.tn-to').value
            });
        }
    });

    const list_thanh_toan = [];
    document.querySelectorAll('.payment-row').forEach(row => {
        if(row.querySelector('.tt-date').value) {
            list_thanh_toan.push({
                date: row.querySelector('.tt-date').value,
                goc: row.querySelector('.tt-goc').value,
                lai: row.querySelector('.tt-lai').value
            });
        }
    });

    const payload = {
        so_tien_vay: parseFloat(document.getElementById('so_tien_vay').value) || 0,
        lai_suat_nam: parseFloat(document.getElementById('lai_suat_nam').value) || 0,
        loai_lai_suat: document.querySelector('input[name="loai_lai_suat"]:checked').value,
        lai_suat_thoa_thuan_qh: document.getElementById('lai_suat_thoa_thuan_qh').value,
        loai_lai_suat_qh: document.querySelector('input[name="loai_lai_suat_qh"]:checked').value,
        phuong_thuc: document.getElementById('phuong_thuc').value,
        thoi_han_nam: parseInt(document.getElementById('thoi_han_nam').value) || 0,
        thoi_han_thang: parseInt(document.getElementById('thoi_han_thang').value) || 0,
        thoi_han_ngay: parseInt(document.getElementById('thoi_han_ngay').value) || 0,
        ngay_vay: document.getElementById('ngay_vay').value,
        ngay_tra_thuc_te: document.getElementById('ngay_tra_thuc_te').value,
        list_tha_noi: list_tha_noi,
        list_thanh_toan: list_thanh_toan
    };

    try {
        const resData = tinhToanChiTiet(payload);
        const matrix = resData.matrix;

        document.getElementById('lblTotalDays').innerText = resData.so_ngay_thuc_te;
        document.getElementById('lblDecomposedText').innerText = resData.decomposed ? resData.decomposed.decompose_text : '';

        document.getElementById('cell_goc_m').innerText = formatVND(matrix.goc.thang);
        document.getElementById('cell_goc_y').innerText = formatVND(matrix.goc.nam);
        document.getElementById('cell_goc_t').innerText = formatVND(matrix.goc.tong);

        document.getElementById('cell_lth_m').innerText = formatVND(matrix.lth.thang);
        document.getElementById('cell_lth_y').innerText = formatVND(matrix.lth.nam);
        document.getElementById('cell_lth_t').innerText = formatVND(matrix.lth.tong);

        document.getElementById('cell_lqh_m').innerText = formatVND(matrix.lqh.thang);
        document.getElementById('cell_lqh_y').innerText = formatVND(matrix.lqh.nam);
        document.getElementById('cell_lqh_t').innerText = formatVND(matrix.lqh.tong);

        document.getElementById('cell_lct_m').innerText = formatVND(matrix.lct.thang);
        document.getElementById('cell_lct_y').innerText = formatVND(matrix.lct.nam);
        document.getElementById('cell_lct_t').innerText = formatVND(matrix.lct.tong);

        document.getElementById('cell_tong_m').innerText = formatVND(matrix.tong.thang);
        document.getElementById('cell_tong_y').innerText = formatVND(matrix.tong.nam);
        document.getElementById('cell_tong_t').innerText = formatVND(matrix.tong.tong);

        document.getElementById('dienGiaiText').innerText = resData.dien_giai;
        document.getElementById('excelDownloadBtn').style.display = 'none';

        document.getElementById('resultBlock').classList.remove('d-none');
        document.getElementById('resultBlock').scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
        alert("Lỗi tính toán: " + err.message);
        console.error(err);
    }
}
```

## Phần 2: INLINE_JS_FUNCTIONS

Chèn toàn bộ code dưới đây ngay trước thẻ `</script>` đóng:

```javascript

// ============================================================
// === PHẦN A: HÀM PHỤ TRỢ NGÀY THÁNG ===
// ============================================================

function parseDate(str) {
    if (!str) return null;
    const parts = str.split('-');
    return new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
}

function addDays(date, days) {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

function daysBetween(d1, d2) {
    return Math.round((d2 - d1) / (24 * 60 * 60 * 1000));
}

function formatDateStr(d) {
    const dd = String(d.getDate()).padStart(2, '0');
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const yyyy = d.getFullYear();
    return dd + '/' + mm + '/' + yyyy;
}

// ============================================================
// === PHẦN B: HÀM TÍNH TOÁN LÃI SUẤT ===
// ============================================================

function getDaysPerYear(date) {
    return date < new Date(2018, 0, 1) ? 360 : 365;
}

function decomposeTotalDays(totalDays, baseDate) {
    const moc2018 = new Date(2018, 0, 1);
    const endDate = addDays(baseDate, totalDays);

    if (baseDate >= moc2018 || endDate <= moc2018) {
        const dpy = getDaysPerYear(baseDate);
        const years = Math.floor(totalDays / dpy);
        const remain = totalDays % dpy;
        return { years: years, months: Math.floor(remain / 30), days: remain % 30 };
    }

    const daysBefore = daysBetween(baseDate, moc2018);
    const daysAfter = totalDays - daysBefore;
    const r1 = decomposeTotalDays(daysBefore, baseDate);
    const r2 = decomposeTotalDays(daysAfter, moc2018);

    let totalD = r1.days + r2.days;
    let totalM = r1.months + r2.months + Math.floor(totalD / 30);
    let totalY = r1.years + r2.years + Math.floor(totalM / 12);
    totalD = totalD % 30;
    totalM = totalM % 12;

    return { years: totalY, months: totalM, days: totalD };
}

function decomposePeriod(startDate, endDate) {
    const totalDays = daysBetween(startDate, endDate);
    if (totalDays <= 0) return { years: 0, months: 0, days: 0 };
    return decomposeTotalDays(totalDays, startDate);
}

function calcInterestFormula(principal, annualRate, years, months, days, baseDate) {
    if (annualRate <= 0 || principal <= 0) {
        return { totalInterest: 0.0, detail: { years: [years, 0.0], months: [months, 0.0], days: [days, 0.0] } };
    }

    const endDate = addDays(baseDate, years * 365 + months * 30 + days);
    const totalDaysTotal = daysBetween(baseDate, endDate);
    const moc2018 = new Date(2018, 0, 1);
    let interestYears = 0.0, interestMonths = 0.0, interestDays = 0.0;

    if (baseDate >= moc2018 || endDate <= moc2018) {
        const dpy = getDaysPerYear(baseDate);
        if (years > 0) interestYears = principal * (annualRate / 100.0) * years;
        if (months > 0) interestMonths = principal * (annualRate / 100.0) * (months / 12.0);
        if (days > 0) interestDays = principal * (annualRate / 100.0) * (days / dpy);
    } else {
        const daysBefore = daysBetween(baseDate, moc2018);
        const daysAfter = totalDaysTotal - daysBefore;

        if (daysBefore > 0) {
            const ybmb = decomposeTotalDays(daysBefore, baseDate);
            if (ybmb.years > 0) interestYears += principal * (annualRate / 100.0) * ybmb.years;
            if (ybmb.months > 0) interestMonths += principal * (annualRate / 100.0) * (ybmb.months / 12.0);
            if (ybmb.days > 0) interestDays += principal * (annualRate / 100.0) * (ybmb.days / 360);
        }
        if (daysAfter > 0) {
            const yama = decomposeTotalDays(daysAfter, moc2018);
            if (yama.years > 0) interestYears += principal * (annualRate / 100.0) * yama.years;
            if (yama.months > 0) interestMonths += principal * (annualRate / 100.0) * (yama.months / 12.0);
            if (yama.days > 0) interestDays += principal * (annualRate / 100.0) * (yama.days / 365);
        }
    }

    return { totalInterest: interestYears + interestMonths + interestDays, detail: { years: [years, interestYears], months: [months, interestMonths], days: [days, interestDays] } };
}

function formatDecomposeText(y, m, d) {
    const parts = [];
    if (y > 0) parts.push(String(y).padStart(2, '0') + ' năm');
    if (m > 0) parts.push(String(m).padStart(2, '0') + ' tháng');
    if (d > 0) parts.push(String(d).padStart(2, '0') + ' ngày');
    return parts.length === 0 ? '00 ngày' : parts.join(' ');
}

function mergeDetail(d1, d2) {
    return {
        years: [d1.years[0] + d2.years[0], d1.years[1] + d2.years[1]],
        months: [d1.months[0] + d2.months[0], d1.months[1] + d2.months[1]],
        days: [d1.days[0] + d2.days[0], d1.days[1] + d2.days[1]]
    };
}

// ============================================================
// === PHẦN C: HÀM CHÍNH tinhToanChiTiet ===
// ============================================================

function tinhToanChiTiet(payload) {
    const so_tien_vay = payload.so_tien_vay;
    const thoi_han_nam = payload.thoi_han_nam;
    const thoi_han_thang = payload.thoi_han_thang;
    const thoi_han_ngay = payload.thoi_han_ngay;
    const lai_suat_nhap = payload.lai_suat_nam;
    const loai_lai_suat = payload.loai_lai_suat;
    const lai_suat_thoa_thuan_qh = payload.lai_suat_thoa_thuan_qh;
    const loai_lai_suat_qh = payload.loai_lai_suat_qh;
    const phuong_thuc = payload.phuong_thuc;
    const ngay_vay = payload.ngay_vay;
    const ngay_tra_thuc_te = payload.ngay_tra_thuc_te;
    const list_tha_noi = payload.list_tha_noi || [];
    const list_thanh_toan = payload.list_thanh_toan || [];

    // 1. XỬ LÝ CÁC MỐC THỜI GIAN CƠ BẢN
    const ngay_vay_dt = parseDate(ngay_vay);
    const ngay_tra_dt = parseDate(ngay_tra_thuc_te);
    const moc_thong_tu_dt = new Date(2018, 0, 1);

    if (!ngay_vay_dt || !ngay_tra_dt) {
        throw new Error('Hệ thống yêu cầu nhập đầy đủ Ngày cho vay và Ngày chốt nợ.');
    }

    // Tính ngày đáo hạn
    let ngay_dao_han_dt = new Date(ngay_vay_dt);
    ngay_dao_han_dt.setFullYear(ngay_dao_han_dt.getFullYear() + thoi_han_nam);
    let thang_hien_tai = ngay_dao_han_dt.getMonth() + 1;
    let nam_hien_tai = ngay_dao_han_dt.getFullYear();
    for (let i = 0; i < thoi_han_thang; i++) {
        thang_hien_tai++;
        if (thang_hien_tai > 12) { thang_hien_tai = 1; nam_hien_tai++; }
    }
    let ngay_tam = ngay_dao_han_dt.getDate();
    while (true) {
        try {
            ngay_dao_han_dt = new Date(nam_hien_tai, thang_hien_tai - 1, ngay_tam);
            if (ngay_dao_han_dt.getMonth() + 1 === thang_hien_tai) break;
            ngay_tam--;
        } catch (e) { ngay_tam--; }
    }
    ngay_dao_han_dt = addDays(ngay_dao_han_dt, thoi_han_ngay);
    const so_ngay_quy_dinh = daysBetween(ngay_vay_dt, ngay_dao_han_dt);

    // 2. XỬ LÝ LÃI SUẤT THẢ NỔI VÀ NHẬT KÝ THANH TOÁN
    const tha_noi_processed = [];
    for (const tn of list_tha_noi) {
        if (tn.rate && tn.from && tn.to) {
            let r = parseFloat(tn.rate);
            if (tn.unit === 'thang') r *= 12;
            tha_noi_processed.push({ rate: r, from: parseDate(tn.from), to: addDays(parseDate(tn.to), 1) });
        }
    }

    const thanh_toan_processed = {};
    for (const tt of list_thanh_toan) {
        if (tt.date) {
            const d_dt = parseDate(tt.date);
            const goc_tra = parseFloat(tt.goc) || 0.0;
            const lai_tra = parseFloat(tt.lai) || 0.0;
            const key = d_dt.getTime();
            if (thanh_toan_processed[key]) {
                thanh_toan_processed[key].goc += goc_tra;
                thanh_toan_processed[key].lai += lai_tra;
            } else {
                thanh_toan_processed[key] = { goc: goc_tra, lai: lai_tra };
            }
        }
    }

    // 3. KHỞI TẠO BIẾN
    let du_no_goc_hien_tai = so_tien_vay;
    const goc_ban_dau_co_dinh = so_tien_vay;
    let tong_lai_trong_han_tich_luy = 0.0;
    let tong_lai_qua_han_tich_luy = 0.0;
    let tong_lai_cham_tra_tich_luy = 0.0;
    let lai_trong_han_chua_tra = 0.0;
    const base_rate_nam = loai_lai_suat === 'thang' ? lai_suat_nhap * 12 : lai_suat_nhap;
    const total_days_simulation = daysBetween(ngay_vay_dt, ngay_tra_dt);
    const tong = decomposePeriod(ngay_vay_dt, ngay_dao_han_dt);

    // 4. CHUẨN BỊ BÁO CÁO
    let dien_giai_text = '=== BÁO CÁO SAO KÊ CHI TIẾT THEO PHƯƠNG PHÁP PHÂN TÁCH NĂM - THÁNG - NGÀY ===\n';
    dien_giai_text += 'THÔNG TIN BAN ĐẦU:\n';
    dien_giai_text += '- Nợ gốc vay: ' + so_tien_vay.toLocaleString('vi-VN') + ' VNĐ\n';
    dien_giai_text += '- Kỳ hạn vay: ' + formatDateStr(ngay_vay_dt) + ' đến ' + formatDateStr(ngay_dao_han_dt) + '\n';
    dien_giai_text += '- Thời hạn vay đã phân tách: ' + formatDecomposeText(tong.years, tong.months, tong.days) + ' (' + so_ngay_quy_dinh + ' ngày)\n';
    dien_giai_text += '='.repeat(60) + '\n\n';

    // 5. XÂY DỰNG SEGMENTS
    const milestonesSet = new Set();
    milestonesSet.add(ngay_vay_dt.getTime());
    milestonesSet.add(ngay_tra_dt.getTime());
    milestonesSet.add(ngay_dao_han_dt.getTime());
    milestonesSet.add(moc_thong_tu_dt.getTime());
    for (const tn of tha_noi_processed) { milestonesSet.add(tn.from.getTime()); milestonesSet.add(tn.to.getTime()); }
    for (const key in thanh_toan_processed) { milestonesSet.add(parseInt(key)); }

    let milestones = Array.from(milestonesSet)
        .map(t => new Date(parseInt(t)))
        .filter(d => d >= ngay_vay_dt && d <= ngay_tra_dt)
        .sort((a, b) => a - b);

    const segments = [];
    for (let i = 0; i < milestones.length - 1; i++) {
        if (milestones[i] < milestones[i + 1]) segments.push({ start: milestones[i], end: milestones[i + 1] });
    }
    if (segments.length === 0 && total_days_simulation > 0) segments.push({ start: ngay_vay_dt, end: ngay_tra_dt });

    // 6. TÍNH TOÁN THEO TỪNG SEGMENT
    let chi_tiet_trong_han = { years: [0, 0.0], months: [0, 0.0], days: [0, 0.0] };
    let chi_tiet_qua_han = { years: [0, 0.0], months: [0, 0.0], days: [0, 0.0] };
    let chi_tiet_cham_tra = { years: [0, 0.0], months: [0, 0.0], days: [0, 0.0] };

    let current_month_str = total_days_simulation > 0 ? String(ngay_vay_dt.getMonth() + 1).padStart(2, '0') + '/' + ngay_vay_dt.getFullYear() : '';
    let m_start_date = ngay_vay_dt;
    let m_goc_dau = du_no_goc_hien_tai;
    let m_lai_trong_han_dau = lai_trong_han_chua_tra;
    let m_lai_trong_han_ps = 0.0, m_lai_qua_han_ps = 0.0, m_lai_cham_tra_ps = 0.0, m_goc_tra = 0.0, m_lai_tra = 0.0;
    let m_nhat_ky_tra = [];

    for (const seg of segments) {
        const seg_start = seg.start;
        const seg_end = seg.end;

        let active_rate = base_rate_nam;
        const mid_point = new Date(seg_start.getTime() + (seg_end - seg_start) / 2);
        for (const tn of tha_noi_processed) {
            if (tn.from <= mid_point && mid_point <= tn.to) { active_rate = tn.rate; break; }
        }
        if (active_rate > 20.0) active_rate = 20.0;

        const is_qua_han = seg_start >= ngay_dao_han_dt;
        const is_cross_due = seg_start < ngay_dao_han_dt && seg_end > ngay_dao_han_dt;

        if (is_cross_due) {
            // Đoạn trong hạn
            const ymd = decomposePeriod(seg_start, ngay_dao_han_dt);
            const co_so_goc = phuong_thuc === 'goc_ban_dau' ? goc_ban_dau_co_dinh : du_no_goc_hien_tai;
            const result = calcInterestFormula(co_so_goc, active_rate, ymd.years, ymd.months, ymd.days, seg_start);
            tong_lai_trong_han_tich_luy += result.totalInterest;
            lai_trong_han_chua_tra += result.totalInterest;
            m_lai_trong_han_ps += result.totalInterest;
            chi_tiet_trong_han = mergeDetail(chi_tiet_trong_han, result.detail);

            // Đoạn quá hạn
            const ymd2 = decomposePeriod(ngay_dao_han_dt, seg_end);
            let rate_qh;
            if (lai_suat_thoa_thuan_qh) {
                rate_qh = parseFloat(lai_suat_thoa_thuan_qh);
                if (loai_lai_suat_qh === 'thang') rate_qh *= 12;
                if (rate_qh > 30.0) rate_qh = 30.0;
            } else {
                rate_qh = active_rate * 1.5;
                if (rate_qh > 30.0) rate_qh = 30.0;
            }
            const lqh_result = calcInterestFormula(du_no_goc_hien_tai, rate_qh, ymd2.years, ymd2.months, ymd2.days, ngay_dao_han_dt);
            tong_lai_qua_han_tich_luy += lqh_result.totalInterest;
            m_lai_qua_han_ps += lqh_result.totalInterest;
            chi_tiet_qua_han = mergeDetail(chi_tiet_qua_han, lqh_result.detail);

            const lct_result = calcInterestFormula(lai_trong_han_chua_tra, 10.0, ymd2.years, ymd2.months, ymd2.days, ngay_dao_han_dt);
            tong_lai_cham_tra_tich_luy += lct_result.totalInterest;
            m_lai_cham_tra_ps += lct_result.totalInterest;
            chi_tiet_cham_tra = mergeDetail(chi_tiet_cham_tra, lct_result.detail);

        } else if (is_qua_han) {
            // Toàn bộ đoạn quá hạn
            const ymd = decomposePeriod(seg_start, seg_end);
            let rate_qh;
            if (lai_suat_thoa_thuan_qh) {
                rate_qh = parseFloat(lai_suat_thoa_thuan_qh);
                if (loai_lai_suat_qh === 'thang') rate_qh *= 12;
                if (rate_qh > 30.0) rate_qh = 30.0;
            } else {
                rate_qh = active_rate * 1.5;
                if (rate_qh > 30.0) rate_qh = 30.0;
            }
            const lqh_result = calcInterestFormula(du_no_goc_hien_tai, rate_qh, ymd.years, ymd.months, ymd.days, seg_start);
            tong_lai_qua_han_tich_luy += lqh_result.totalInterest;
            m_lai_qua_han_ps += lqh_result.totalInterest;
            chi_tiet_qua_han = mergeDetail(chi_tiet_qua_han, lqh_result.detail);

            const lct_result = calcInterestFormula(lai_trong_han_chua_tra, 10.0, ymd.years, ymd.months, ymd.days, seg_start);
            tong_lai_cham_tra_tich_luy += lct_result.totalInterest;
            m_lai_cham_tra_ps += lct_result.totalInterest;
            chi_tiet_cham_tra = mergeDetail(chi_tiet_cham_tra, lct_result.detail);

        } else {
            // Đoạn trong hạn
            const ymd = decomposePeriod(seg_start, seg_end);
            const co_so_goc = phuong_thuc === 'goc_ban_dau' ? goc_ban_dau_co_dinh : du_no_goc_hien_tai;
            const result = calcInterestFormula(co_so_goc, active_rate, ymd.years, ymd.months, ymd.days, seg_start);
            tong_lai_trong_han_tich_luy += result.totalInterest;
            lai_trong_han_chua_tra += result.totalInterest;
            m_lai_trong_han_ps += result.totalInterest;
            chi_tiet_trong_han = mergeDetail(chi_tiet_trong_han, result.detail);
        }

        // XỬ LÝ THANH TOÁN TẠI MỐC SEGMENT
        const seg_end_key = seg_end.getTime();
        if (thanh_toan_processed[seg_end_key]) {
            const tt = thanh_toan_processed[seg_end_key];
            m_goc_tra += tt.goc;
            m_lai_tra += tt.lai;
            m_nhat_ky_tra.push({ date: formatDateStr(seg_end), goc: tt.goc, lai: tt.lai });

            // Đối trừ: trừ gốc, trừ lãi
            if (tt.lai > 0) {
                let lai_con_lai = tt.lai;
                if (lai_trong_han_chua_tra > 0) {
                    const tru_lth = Math.min(lai_con_lai, lai_trong_han_chua_tra);
                    lai_trong_han_chua_tra -= tru_lth;
                    lai_con_lai -= tru_lth;
                }
                if (lai_con_lai > 0 && tong_lai_cham_tra_tich_luy > 0) {
                    // Giảm lãi chậm trả
                }
            }
            if (tt.goc > 0) {
                du_no_goc_hien_tai = Math.max(0, du_no_goc_hien_tai - tt.goc);
            }
        }

        // CHỐT SỔ THÁNG
        const seg_month_str = String(seg_end.getMonth() + 1).padStart(2, '0') + '/' + seg_end.getFullYear();
        if (seg_month_str !== current_month_str || seg === segments[segments.length - 1]) {
            if (m_goc_dau > 0 || m_lai_trong_han_ps > 0 || m_lai_qua_han_ps > 0 || m_lai_cham_tra_ps > 0 || m_goc_tra > 0 || m_lai_tra > 0) {
                dien_giai_text += '--- Tháng ' + current_month_str + ' ---\n';
                dien_giai_text += '  Dư nợ đầu kỳ: ' + m_goc_dau.toLocaleString('vi-VN') + ' VNĐ\n';
                dien_giai_text += '  Lãi trong hạn phát sinh: ' + m_lai_trong_han_ps.toLocaleString('vi-VN') + ' VNĐ\n';
                dien_giai_text += '  Lãi quá hạn phát sinh: ' + m_lai_qua_han_ps.toLocaleString('vi-VN') + ' VNĐ\n';
                dien_giai_text += '  Lãi chậm trả phát sinh: ' + m_lai_cham_tra_ps.toLocaleString('vi-VN') + ' VNĐ\n';
                if (m_nhat_ky_tra.length > 0) {
                    for (const nk of m_nhat_ky_tra) {
                        dien_giai_text += '  >> Thanh toán ngày ' + nk.date + ': Gốc ' + nk.goc.toLocaleString('vi-VN') + ' VNĐ, Lãi ' + nk.lai.toLocaleString('vi-VN') + ' VNĐ\n';
                    }
                }
                dien_giai_text += '  Dư nợ cuối kỳ: ' + du_no_goc_hien_tai.toLocaleString('vi-VN') + ' VNĐ\n\n';
            }

            // Reset tháng
            current_month_str = seg_month_str;
            m_start_date = seg_end;
            m_goc_dau = du_no_goc_hien_tai;
            m_lai_trong_han_dau = lai_trong_han_chua_tra;
            m_lai_trong_han_ps = 0.0;
            m_lai_qua_han_ps = 0.0;
            m_lai_cham_tra_ps = 0.0;
            m_goc_tra = 0.0;
            m_lai_tra = 0.0;
            m_nhat_ky_tra = [];
        }
    }

    // 7. TỔNG KẾT
    dien_giai_text += '=== TỔNG KẾT ===\n';
    dien_giai_text += 'Tổng lãi trong hạn: ' + tong_lai_trong_han_tich_luy.toLocaleString('vi-VN') + ' VNĐ\n';
    dien_giai_text += 'Tổng lãi quá hạn: ' + tong_lai_qua_han_tich_luy.toLocaleString('vi-VN') + ' VNĐ\n';
    dien_giai_text += 'Tổng lãi chậm trả: ' + tong_lai_cham_tra_tich_luy.toLocaleString('vi-VN') + ' VNĐ\n';
    dien_giai_text += 'Tổng cộng lãi: ' + (tong_lai_trong_han_tich_luy + tong_lai_qua_han_tich_luy + tong_lai_cham_tra_tich_luy).toLocaleString('vi-VN') + ' VNĐ\n';
    dien_giai_text += 'Dư nợ gốc còn lại: ' + du_no_goc_hien_tai.toLocaleString('vi-VN') + ' VNĐ\n';

    // 8. MA TRẬN KẾT QUẢ
    const matrix = {
        goc: { thang: du_no_goc_hien_tai, nam: du_no_goc_hien_tai, tong: du_no_goc_hien_tai },
        lth: { thang: tong_lai_trong_han_tich_luy, nam: tong_lai_trong_han_tich_luy, tong: tong_lai_trong_han_tich_luy },
        lqh: { thang: tong_lai_qua_han_tich_luy, nam: tong_lai_qua_han_tich_luy, tong: tong_lai_qua_han_tich_luy },
        lct: { thang: tong_lai_cham_tra_tich_luy, nam: tong_lai_cham_tra_tich_luy, tong: tong_lai_cham_tra_tich_luy },
        tong: { thang: tong_lai_trong_han_tich_luy + tong_lai_qua_han_tich_luy + tong_lai_cham_tra_tich_luy, nam: tong_lai_trong_han_tich_luy + tong_lai_qua_han_tich_luy + tong_lai_cham_tra_tich_luy, tong: tong_lai_trong_han_tich_luy + tong_lai_qua_han_tich_luy + tong_lai_cham_tra_tich_luy }
    };

    return {
        matrix: matrix,
        so_ngay_thuc_te: total_days_simulation,
        decomposed: { decompose_text: formatDecomposeText(tong.years, tong.months, tong.days) },
        dien_giai: dien_giai_text
    };
}
```
