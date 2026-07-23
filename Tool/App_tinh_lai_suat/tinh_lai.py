import os
from datetime import datetime, timedelta
import pandas as pd

# --- HÀM PHỤ ---

def get_days_per_year(date):
    """Trả về số ngày/năm: 360 nếu trước 01/01/2018, 365 nếu từ 01/01/2018."""
    return 360 if date < datetime(2018, 1, 1) else 365

def decompose_total_days(total_days, base_date):
    """
    Phân tách tổng số ngày thành (năm, tháng, ngày) dựa trên ngày cơ sở.
    - 1 năm = 365 hoặc 360 ngày (tùy base_date so với 2018)
    - 1 tháng = 30 ngày
    
    Có thể vắt qua mốc 2018 → tách làm 2 đoạn.
    """
    moc_2018 = datetime(2018, 1, 1)
    end_date = base_date + timedelta(days=total_days)
    
    # Nếu khoảng không vắt qua 2018
    if base_date >= moc_2018 or end_date <= moc_2018:
        dpy = get_days_per_year(base_date)
        years = total_days // dpy
        remain = total_days % dpy
        months = remain // 30
        days = remain % 30
        return (years, months, days)
    
    # Vắt qua mốc 2018 → tách 2 đoạn
    days_before = (moc_2018 - base_date).days
    days_after = total_days - days_before
    
    y1, m1, d1 = decompose_total_days(days_before, base_date)
    y2, m2, d2 = decompose_total_days(days_after, moc_2018)
    
    total_y = y1 + y2
    total_m = m1 + m2
    total_d = d1 + d2
    
    # Chuẩn hóa: nếu ngày >= 30 → chuyển sang tháng
    if total_d >= 30:
        total_m += total_d // 30
        total_d = total_d % 30
    # Nếu tháng >= 12 → chuyển sang năm (nhưng thường không cần vì đã tách 2 đoạn)
    if total_m >= 12:
        total_y += total_m // 12
        total_m = total_m % 12
    
    return (total_y, total_m, total_d)


def decompose_period(start_date, end_date):
    """
    Phân tách một khoảng thời gian (start → end) thành (năm, tháng, ngày).
    """
    total_days = (end_date - start_date).days
    if total_days <= 0:
        return (0, 0, 0)
    return decompose_total_days(total_days, start_date)


def calc_interest_formula(principal, annual_rate, years, months, days, base_date):
    """
    Tính lãi theo công thức phân tách Năm-Tháng-Ngày.
    Có tính đến 360/365 theo giai đoạn.
    
    Returns: (tong_lai, chi_tiet_dict)
        chi_tiet_dict = {
            'years': (y, interest_y),
            'months': (m, interest_m),
            'days': (d, interest_d)
        }
    """
    if annual_rate <= 0 or principal <= 0:
        return (0.0, {'years': (years, 0.0), 'months': (months, 0.0), 'days': (days, 0.0)})
    
    # Tính từng phần riêng biệt theo đúng quy ước
    # Với đoạn thời gian có thể vắt qua 2018, ta cần tính chính xác
    
    end_date = base_date + timedelta(days=(years * 365 + months * 30 + days))
    total_days_total = (end_date - base_date).days
    
    # Phân tách thành các đoạn không vắt qua 2018
    moc_2018 = datetime(2018, 1, 1)
    
    interest_years = 0.0
    interest_months = 0.0
    interest_days = 0.0
    
    # Xử lý năm và tháng và ngày đã được phân tách
    # Tính lãi = Gốc × rate × (years + months/12 + days/dpy)
    # Với dpy phụ thuộc vào từng đoạn
    
    # Nếu toàn bộ nằm 1 bên mốc 2018
    if base_date >= moc_2018 or end_date <= moc_2018:
        dpy = get_days_per_year(base_date)
        # Phần năm
        if years > 0:
            interest_years = principal * (annual_rate / 100.0) * years
        # Phần tháng (1 tháng = 1/12 năm)
        if months > 0:
            interest_months = principal * (annual_rate / 100.0) * (months / 12.0)
        # Phần ngày
        if days > 0:
            interest_days = principal * (annual_rate / 100.0) * (days / float(dpy))
    else:
        # Vắt qua 2018 → tách riêng
        days_before = (moc_2018 - base_date).days
        days_after = total_days_total - days_before
        
        # Đoạn trước 2018: dpy = 360
        if days_before > 0:
            yb, mb, db = decompose_total_days(days_before, base_date)
            dpy_before = 360
            if yb > 0:
                interest_years += principal * (annual_rate / 100.0) * yb
            if mb > 0:
                interest_months += principal * (annual_rate / 100.0) * (mb / 12.0)
            if db > 0:
                interest_days += principal * (annual_rate / 100.0) * (db / float(dpy_before))
        
        # Đoạn sau 2018: dpy = 365
        if days_after > 0:
            actual_end = base_date + timedelta(days=total_days_total)
            ya, ma, da = decompose_total_days(days_after, moc_2018)
            dpy_after = 365
            if ya > 0:
                interest_years += principal * (annual_rate / 100.0) * ya
            if ma > 0:
                interest_months += principal * (annual_rate / 100.0) * (ma / 12.0)
            if da > 0:
                interest_days += principal * (annual_rate / 100.0) * (da / float(dpy_after))
    
    total_interest = interest_years + interest_months + interest_days
    
    return (total_interest, {
        'years': (years, interest_years),
        'months': (months, interest_months),
        'days': (days, interest_days)
    })


def format_decompose_text(y, m, d, base_date):
    """Tạo text mô tả phân tách."""
    parts = []
    if y > 0:
        parts.append(f"{y:02d} năm")
    if m > 0:
        parts.append(f"{m:02d} tháng")
    if d > 0:
        parts.append(f"{d:02d} ngày")
    if not parts:
        return "00 ngày"
    return " ".join(parts)


def tinh_toan_chi_tiet(so_tien_vay, thoi_han_nam, thoi_han_thang, thoi_han_ngay, lai_suat_nhap, loai_lai_suat, 
                      lai_suat_thoa_thuan_qh, loai_lai_suat_qh, phuong_thuc, ngay_vay, ngay_tra_thuc_te, 
                      list_tha_noi=None, list_thanh_toan=None):
    
    # 1. XỬ LÝ CÁC MỐC THỜI GIAN CƠ BẢN
    ngay_vay_dt = datetime.strptime(ngay_vay, '%Y-%m-%d')
    ngay_tra_dt = datetime.strptime(ngay_tra_thuc_te, '%Y-%m-%d')
    moc_thong_tu_dt = datetime.strptime('2018-01-01', '%Y-%m-%d')
    
    try:
        ngay_dao_han_dt = ngay_vay_dt.replace(year=ngay_vay_dt.year + thoi_han_nam)
    except ValueError:
        ngay_dao_han_dt = ngay_vay_dt + timedelta(days=365 * thoi_han_nam)
    
    thang_hien_tai = ngay_dao_han_dt.month
    nam_hien_tai = ngay_dao_han_dt.year
    for _ in range(thoi_han_thang):
        thang_hien_tai += 1
        if thang_hien_tai > 12:
            thang_hien_tai = 1
            nam_hien_tai += 1
            
    ngay_tam = ngay_dao_han_dt.day
    while True:
        try:
            ngay_dao_han_dt = ngay_dao_han_dt.replace(year=nam_hien_tai, month=thang_hien_tai, day=ngay_tam)
            break
        except ValueError:
            ngay_tam -= 1
    ngay_dao_han_dt += timedelta(days=thoi_han_ngay)
    so_ngay_quy_dinh = (ngay_dao_han_dt - ngay_vay_dt).days
    
    # 2. XỬ LÝ DỮ LIỆU LÃI SUẤT THẢ NỔI VÀ NHẬT KÝ THANH TOÁN
    tha_noi_processed = []
    if list_tha_noi:
        for tn in list_tha_noi:
            if tn.get('rate') and tn.get('from') and tn.get('to'):
                r = float(tn['rate'])
                if tn.get('unit') == 'thang': r *= 12
                tha_noi_processed.append({
                    'rate': r,
                    'from': datetime.strptime(tn['from'], '%Y-%m-%d'),
                    'to': datetime.strptime(tn['to'], '%Y-%m-%d')
                })
                
    thanh_toan_processed = {}
    if list_thanh_toan:
        for tt in list_thanh_toan:
            if tt.get('date'):
                d_dt = datetime.strptime(tt['date'], '%Y-%m-%d')
                goc_tra = float(tt['goc']) if tt.get('goc') else 0.0
                lai_tra = float(tt['lai']) if tt.get('lai') else 0.0
                if d_dt in thanh_toan_processed:
                    thanh_toan_processed[d_dt]['goc'] += goc_tra
                    thanh_toan_processed[d_dt]['lai'] += lai_tra
                else:
                    thanh_toan_processed[d_dt] = {'goc': goc_tra, 'lai': lai_tra}

    # 3. KHỞI TẠO BIẾN
    du_no_goc_hien_tai = so_tien_vay
    goc_ban_dau_co_dinh = so_tien_vay
    
    tong_lai_trong_han_tich_luy = 0.0
    tong_lai_qua_han_tich_luy = 0.0
    tong_lai_cham_tra_tich_luy = 0.0
    lai_trong_han_chua_tra = 0.0
    
    base_rate_nam = lai_suat_nhap * 12 if loai_lai_suat == 'thang' else lai_suat_nhap
    total_days_simulation = (ngay_tra_dt - ngay_vay_dt).days
    
    # ---- Phân tách tổng thời hạn vay ----
    tong_y, tong_m, tong_d = decompose_period(ngay_vay_dt, ngay_dao_han_dt)
    
    # 4. CHUẨN BỊ XUẤT BÁO CÁO
    dien_giai_text = "=== BÁO CÁO SAO KÊ CHI TIẾT THEO PHƯƠNG PHÁP PHÂN TÁCH NĂM - THÁNG - NGÀY ===\n"
    dien_giai_text += f"THÔNG TIN BAN ĐẦU:\n"
    dien_giai_text += f"- Nợ gốc vay: {so_tien_vay:,.0f} VNĐ\n"
    dien_giai_text += f"- Kỳ hạn vay: {ngay_vay_dt.strftime('%d/%m/%Y')} đến {ngay_dao_han_dt.strftime('%d/%m/%Y')}\n"
    dien_giai_text += f"- Thời hạn vay đã phân tách: {format_decompose_text(tong_y, tong_m, tong_d, ngay_vay_dt)} ({so_ngay_quy_dinh} ngày)\n"
    dien_giai_text += "="*60 + "\n\n"
    
    txt_lai_qh_excel = f"{lai_suat_thoa_thuan_qh} %/{loai_lai_suat_qh}" if lai_suat_thoa_thuan_qh else 'Mặc định bằng 150% lãi trong hạn'
    excel_rows = [
        {"Hạng mục": "--- THÔNG TIN VỀ KHOẢN VAY VÀ LÃI SUẤT THỎA THUẬN BAN ĐẦU ---", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""},
        {"Hạng mục": "Số tiền gốc vay ban đầu", "Nội dung chi tiết": ngay_vay_dt.strftime('%d/%m/%Y'), "Giá trị (VNĐ)": f"{so_tien_vay:,.0f}"},
        {"Hạng mục": "Ngày tất toán khoản vay", "Nội dung chi tiết": ngay_tra_dt.strftime('%d/%m/%Y'), "Giá trị (VNĐ)": ""},
        {"Hạng mục": "Lãi suất trong hạn", "Nội dung chi tiết": f"{lai_suat_nhap} %/{loai_lai_suat}", "Giá trị (VNĐ)": ""},
        {"Hạng mục": "Lãi suất quá hạn", "Nội dung chi tiết": txt_lai_qh_excel, "Giá trị (VNĐ)": ""},
        {"Hạng mục": "Ngày đáo hạn dự kiến", "Nội dung chi tiết": ngay_dao_han_dt.strftime('%d/%m/%Y'), "Giá trị (VNĐ)": ""},
        {"Hạng mục": f"Thời hạn vay phân tách", "Nội dung chi tiết": format_decompose_text(tong_y, tong_m, tong_d, ngay_vay_dt), "Giá trị (VNĐ)": ""},
        {"Hạng mục": "", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""},
        {"Hạng mục": "--- BÁO CÁO SAO KÊ DÒNG TIỀN VÀ ĐỐI TRỪ CHI TIẾT THEO THÁNG ---", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""}
    ]

    # 5. XÂY DỰNG DANH SÁCH CÁC ĐOẠN THỜI GIAN (SEGMENTS)
    # Thu thập tất cả các mốc quan trọng
    milestones = set()
    milestones.add(ngay_vay_dt)
    milestones.add(ngay_tra_dt)
    milestones.add(ngay_dao_han_dt)
    milestones.add(moc_thong_tu_dt)
    
    # Mốc từ thả nổi
    for tn in tha_noi_processed:
        milestones.add(tn['from'])
        milestones.add(tn['to'] + timedelta(days=1))  # ngày kết thúc + 1
    
    # Mốc từ thanh toán
    for d in thanh_toan_processed.keys():
        milestones.add(d)
    
    # Lọc các mốc trong khoảng [ngay_vay, ngay_tra]
    milestones = sorted([m for m in milestones if ngay_vay_dt <= m <= ngay_tra_dt])
    
    # Tạo các segment
    segments = []
    for i in range(len(milestones) - 1):
        seg_start = milestones[i]
        seg_end = milestones[i + 1]
        if seg_start < seg_end:
            segments.append((seg_start, seg_end))
    
    # Nếu không có segment nào (có thể xảy ra khi milestones chỉ có 1 điểm)
    if not segments and total_days_simulation > 0:
        segments.append((ngay_vay_dt, ngay_tra_dt))
    
    # 6. TÍNH TOÁN THEO TỪNG SEGMENT
    # Lưu chi tiết phân tách cho hiển thị cuối cùng
    chi_tiet_trong_han = {'years': (0, 0.0), 'months': (0, 0.0), 'days': (0, 0.0)}
    chi_tiet_qua_han = {'years': (0, 0.0), 'months': (0, 0.0), 'days': (0, 0.0)}
    chi_tiet_cham_tra = {'years': (0, 0.0), 'months': (0, 0.0), 'days': (0, 0.0)}
    
    # Biến cho báo cáo tháng
    current_month_str = ngay_vay_dt.strftime('%m/%Y') if total_days_simulation > 0 else ""
    m_start_date = ngay_vay_dt
    m_goc_dau = du_no_goc_hien_tai
    m_lai_trong_han_dau = lai_trong_han_chua_tra
    m_lai_trong_han_ps = 0.0
    m_lai_qua_han_ps = 0.0
    m_lai_cham_tra_ps = 0.0
    m_goc_tra = 0.0
    m_lai_tra = 0.0
    m_nhat_ky_tra = []
    
    for seg_start, seg_end in segments:
        # Xác định lãi suất áp dụng cho segment này
        active_rate = base_rate_nam
        mid_point = seg_start + (seg_end - seg_start) / 2
        for tn in tha_noi_processed:
            if tn['from'] <= mid_point <= tn['to']:
                active_rate = tn['rate']
                break
        if active_rate > 20.0:
            active_rate = 20.0
        
        # Kiểm tra trong hạn / quá hạn
        is_qua_han = (seg_start >= ngay_dao_han_dt)
        # Có thể segment bắt đầu trong hạn và kết thúc quá hạn
        is_cross_due = (seg_start < ngay_dao_han_dt and seg_end > ngay_dao_han_dt)
        
        if is_cross_due:
            # Tách làm 2 đoạn: trong hạn và quá hạn
            seg_trong_han = (seg_start, ngay_dao_han_dt)
            seg_qua_han = (ngay_dao_han_dt, seg_end)
            
            # Đoạn trong hạn
            loans_start = seg_trong_han[0]
            loans_end = seg_trong_han[1]
            y_in, m_in, d_in = decompose_period(loans_start, loans_end)
            co_so_goc = goc_ban_dau_co_dinh if phuong_thuc == "goc_ban_dau" else du_no_goc_hien_tai
            total_int, detail = calc_interest_formula(co_so_goc, active_rate, y_in, m_in, d_in, loans_start)
            tong_lai_trong_han_tich_luy += total_int
            lai_trong_han_chua_tra += total_int
            m_lai_trong_han_ps += total_int
            chi_tiet_trong_han = _merge_detail(chi_tiet_trong_han, detail)
            
            # Đoạn quá hạn
            loans_start = seg_qua_han[0]
            loans_end = seg_qua_han[1]
            y_out, m_out, d_out = decompose_period(loans_start, loans_end)
            
            # Lãi quá hạn
            if lai_suat_thoa_thuan_qh:
                rate_qh = float(lai_suat_thoa_thuan_qh)
                if loai_lai_suat_qh == 'thang':
                    rate_qh *= 12
                if rate_qh > 30.0:
                    rate_qh = 30.0
            else:
                rate_qh = active_rate * 1.5
                if rate_qh > 30.0:
                    rate_qh = 30.0
            
            lqh_val, lqh_detail = calc_interest_formula(du_no_goc_hien_tai, rate_qh, y_out, m_out, d_out, loans_start)
            tong_lai_qua_han_tich_luy += lqh_val
            m_lai_qua_han_ps += lqh_val
            chi_tiet_qua_han = _merge_detail(chi_tiet_qua_han, lqh_detail)
            
            # Lãi chậm trả
            lct_val, lct_detail = calc_interest_formula(lai_trong_han_chua_tra, 10.0, y_out, m_out, d_out, loans_start)
            tong_lai_cham_tra_tich_luy += lct_val
            m_lai_cham_tra_ps += lct_val
            chi_tiet_cham_tra = _merge_detail(chi_tiet_cham_tra, lct_detail)
            
        elif not is_qua_han:
            # Toàn bộ đoạn trong hạn
            y_s, m_s, d_s = decompose_period(seg_start, seg_end)
            co_so_goc = goc_ban_dau_co_dinh if phuong_thuc == "goc_ban_dau" else du_no_goc_hien_tai
            total_int, detail = calc_interest_formula(co_so_goc, active_rate, y_s, m_s, d_s, seg_start)
            tong_lai_trong_han_tich_luy += total_int
            lai_trong_han_chua_tra += total_int
            m_lai_trong_han_ps += total_int
            chi_tiet_trong_han = _merge_detail(chi_tiet_trong_han, detail)
        else:
            # Toàn bộ đoạn quá hạn
            y_s, m_s, d_s = decompose_period(seg_start, seg_end)
            
            if lai_suat_thoa_thuan_qh:
                rate_qh = float(lai_suat_thoa_thuan_qh)
                if loai_lai_suat_qh == 'thang':
                    rate_qh *= 12
                if rate_qh > 30.0:
                    rate_qh = 30.0
            else:
                rate_qh = active_rate * 1.5
                if rate_qh > 30.0:
                    rate_qh = 30.0
            
            lqh_val, lqh_detail = calc_interest_formula(du_no_goc_hien_tai, rate_qh, y_s, m_s, d_s, seg_start)
            tong_lai_qua_han_tich_luy += lqh_val
            m_lai_qua_han_ps += lqh_val
            chi_tiet_qua_han = _merge_detail(chi_tiet_qua_han, lqh_detail)
            
            lct_val, lct_detail = calc_interest_formula(lai_trong_han_chua_tra, 10.0, y_s, m_s, d_s, seg_start)
            tong_lai_cham_tra_tich_luy += lct_val
            m_lai_cham_tra_ps += lct_val
            chi_tiet_cham_tra = _merge_detail(chi_tiet_cham_tra, lct_detail)
        
        # Xử lý thanh toán nếu có tại điểm cuối segment
        if seg_end in thanh_toan_processed:
            pay_info = thanh_toan_processed[seg_end]
            g_paid = pay_info['goc']
            l_paid = pay_info['lai']
            m_goc_tra += g_paid
            m_lai_tra += l_paid
            m_nhat_ky_tra.append(f"Ngày {seg_end.strftime('%d/%m/%Y')}: Trả Gốc {g_paid:,.0f}đ, Trả Lãi {l_paid:,.0f}đ")
            du_no_goc_hien_tai = max(0.0, du_no_goc_hien_tai - g_paid)
            lai_trong_han_chua_tra = max(0.0, lai_trong_han_chua_tra - l_paid)
        
        # Chốt sổ cuối tháng: kiểm tra nếu segment kết thúc vào tháng mới hoặc là segment cuối
        is_month_end = (seg_end.month != m_start_date.month) or (seg_end == ngay_tra_dt)
        
        if is_month_end:
            m_end_date = seg_end
            tong_ps_thang = m_lai_trong_han_ps + m_lai_qua_han_ps + m_lai_cham_tra_ps
            
            # Tạo văn bản hiển thị
            thang_text = f"🗓️ KỲ SAO KÊ THÁNG: {current_month_str} (Từ ngày {m_start_date.strftime('%d/%m/%Y')} đến {m_end_date.strftime('%d/%m/%Y')})\n"
            
            thang_text += f"  ▶ [ĐẦU KỲ] Dư nợ tồn đọng chuyển sang:\n"
            thang_text += f"    - Nợ gốc: {m_goc_dau:,.0f} VNĐ\n"
            thang_text += f"    - Lãi tồn đọng: {m_lai_trong_han_dau:,.0f} VNĐ\n"
            
            thang_text += f"  ▶ [PHÁT SINH PHẢI TRẢ] Nghĩa vụ phát sinh thêm trong tháng này: +{tong_ps_thang:,.0f} VNĐ\n"
            if m_lai_trong_han_ps > 0:
                thang_text += f"    - Tiền lãi trong hạn: +{m_lai_trong_han_ps:,.0f} VNĐ\n"
            if m_lai_qua_han_ps > 0:
                thang_text += f"    - Tiền lãi quá hạn (tính trên gốc): +{m_lai_qua_han_ps:,.0f} VNĐ\n"
            if m_lai_cham_tra_ps > 0:
                thang_text += f"    - Tiền lãi chậm trả (tính trên lãi): +{m_lai_cham_tra_ps:,.0f} VNĐ\n"
                
            thang_text += f"  ▶ [ĐÃ THANH TOÁN] Đương sự nộp trả thực tế trong tháng: Gốc đã trả {m_goc_tra:,.0f} VNĐ | Lãi đã trả {m_lai_tra:,.0f} VNĐ\n"
            if m_nhat_ky_tra:
                for nk in m_nhat_ky_tra:
                    thang_text += f"    ↳ Chi tiết: {nk}\n"
            else:
                thang_text += f"    ↳ (Không có giao dịch thanh toán nào trong tháng này)\n"
                
            thang_text += f"  ▶ [CUỐI KỲ CÒN LẠI] Dư nợ chốt cuối tháng chuyển sang kỳ sau:\n"
            thang_text += f"    - Nợ gốc còn lại: {du_no_goc_hien_tai:,.0f} VNĐ\n"
            thang_text += f"    - Lãi trong hạn còn lại: {lai_trong_han_chua_tra:,.0f} VNĐ\n"
            thang_text += "-"*60 + "\n"
            
            dien_giai_text += thang_text
            
            # Excel rows
            excel_rows.append({"Hạng mục": f"--- CHI TIẾT THÁNG {current_month_str} ---", "Nội dung chi tiết": f"Từ {m_start_date.strftime('%d/%m/%Y')} đến {m_end_date.strftime('%d/%m/%Y')}", "Giá trị (VNĐ)": ""})
            excel_rows.append({"Hạng mục": "[ĐẦU KỲ] Dư nợ gốc", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_goc_dau:,.0f}"})
            excel_rows.append({"Hạng mục": "[ĐẦU KỲ] Lãi tồn đọng", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_lai_trong_han_dau:,.0f}"})
            excel_rows.append({"Hạng mục": "[PHÁT SINH PHẢI TRẢ] Lãi trong hạn", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_lai_trong_han_ps:,.0f}"})
            excel_rows.append({"Hạng mục": "[PHÁT SINH PHẢI TRẢ] Lãi quá hạn", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_lai_qua_han_ps:,.0f}"})
            excel_rows.append({"Hạng mục": "[PHÁT SINH PHẢI TRẢ] Lãi chậm trả", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_lai_cham_tra_ps:,.0f}"})
            excel_rows.append({"Hạng mục": "[ĐÃ THANH TOÁN] Tiền gốc nộp trả", "Nội dung chi tiết": " | ".join(m_nhat_ky_tra) if m_nhat_ky_tra else "Không phát sinh", "Giá trị (VNĐ)": f"{m_goc_tra:,.0f}"})
            excel_rows.append({"Hạng mục": "[ĐÃ THANH TOÁN] Tiền lãi nộp trả", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{m_lai_tra:,.0f}"})
            excel_rows.append({"Hạng mục": "[CUỐI KỲ CÒN LẠI] Dư nợ gốc", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{du_no_goc_hien_tai:,.0f}"})
            excel_rows.append({"Hạng mục": "[CUỐI KỲ CÒN LẠI] Lãi tồn đọng", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{lai_trong_han_chua_tra:,.0f}"})
            excel_rows.append({"Hạng mục": "", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""})
            
            # Reset biến cho tháng tiếp theo
            if seg_end < ngay_tra_dt:
                current_month_str = seg_end.strftime('%m/%Y')
                m_start_date = seg_end
                m_goc_dau = du_no_goc_hien_tai
                m_lai_trong_han_dau = lai_trong_han_chua_tra
                m_lai_trong_han_ps = 0.0
                m_lai_qua_han_ps = 0.0
                m_lai_cham_tra_ps = 0.0
                m_goc_tra = 0.0
                m_lai_tra = 0.0
                m_nhat_ky_tra = []

    # 7. TỔNG KẾT KẾT QUẢ CUỐI CÙNG
    y_in_total, m_in_total, d_in_total = chi_tiet_trong_han['years'][0], chi_tiet_trong_han['months'][0], chi_tiet_trong_han['days'][0]
    i_y_in, i_m_in, i_d_in = chi_tiet_trong_han['years'][1], chi_tiet_trong_han['months'][1], chi_tiet_trong_han['days'][1]
    
    y_out_total, m_out_total, d_out_total = chi_tiet_qua_han['years'][0], chi_tiet_qua_han['months'][0], chi_tiet_qua_han['days'][0]
    i_y_out, i_m_out, i_d_out = chi_tiet_qua_han['years'][1], chi_tiet_qua_han['months'][1], chi_tiet_qua_han['days'][1]
    
    y_ct_total, m_ct_total, d_ct_total = chi_tiet_cham_tra['years'][0], chi_tiet_cham_tra['months'][0], chi_tiet_cham_tra['days'][0]
    i_y_ct, i_m_ct, i_d_ct = chi_tiet_cham_tra['years'][1], chi_tiet_cham_tra['months'][1], chi_tiet_cham_tra['days'][1]
    
    # Tổng hợp hiển thị phân tách
    dien_giai_text += f"\n=== KẾT QUẢ TỔNG HỢP THEO PHƯƠNG PHÁP PHÂN TÁCH NĂM - THÁNG - NGÀY ===\n\n"
    
    dien_giai_text += f"📌 LÃI TRONG HẠN:\n"
    if y_in_total > 0:
        dien_giai_text += f"   - Lãi của {y_in_total:02d} năm: {i_y_in:,.0f} VNĐ\n"
    if m_in_total > 0:
        dien_giai_text += f"   - Lãi của {m_in_total:02d} tháng: {i_m_in:,.0f} VNĐ\n"
    if d_in_total > 0:
        dien_giai_text += f"   - Lãi của {d_in_total:02d} ngày: {i_d_in:,.0f} VNĐ\n"
    dien_giai_text += f"   → Tổng lãi trong hạn tồn đọng: {lai_trong_han_chua_tra:,.0f} VNĐ\n\n"
    
    dien_giai_text += f"📌 LÃI QUÁ HẠN (trên gốc):\n"
    if y_out_total > 0:
        dien_giai_text += f"   - Lãi của {y_out_total:02d} năm: {i_y_out:,.0f} VNĐ\n"
    if m_out_total > 0:
        dien_giai_text += f"   - Lãi của {m_out_total:02d} tháng: {i_m_out:,.0f} VNĐ\n"
    if d_out_total > 0:
        dien_giai_text += f"   - Lãi của {d_out_total:02d} ngày: {i_d_out:,.0f} VNĐ\n"
    dien_giai_text += f"   → Tổng lãi quá hạn tích lũy: {tong_lai_qua_han_tich_luy:,.0f} VNĐ\n\n"
    
    dien_giai_text += f"📌 LÃI CHẬM TRẢ (trên lãi):\n"
    if y_ct_total > 0:
        dien_giai_text += f"   - Lãi của {y_ct_total:02d} năm: {i_y_ct:,.0f} VNĐ\n"
    if m_ct_total > 0:
        dien_giai_text += f"   - Lãi của {m_ct_total:02d} tháng: {i_m_ct:,.0f} VNĐ\n"
    if d_ct_total > 0:
        dien_giai_text += f"   - Lãi của {d_ct_total:02d} ngày: {i_d_ct:,.0f} VNĐ\n"
    dien_giai_text += f"   → Tổng lãi chậm trả tích lũy: {tong_lai_cham_tra_tich_luy:,.0f} VNĐ\n\n"
    
    tong_cong_nghia_vu = du_no_goc_hien_tai + lai_trong_han_chua_tra + tong_lai_qua_han_tich_luy + tong_lai_cham_tra_tich_luy
    dien_giai_text += f"💰 TỔNG NGHĨA VỤ TÀI CHÍNH CHỐT SAU ĐỐI TRỪ: {tong_cong_nghia_vu:,.0f} VNĐ\n"
    dien_giai_text += f"{'='*60}\n"
    dien_giai_text += f"Tổng thời gian tính toán: {total_days_simulation} ngày "
    dien_giai_text += f"(tương đương: {format_decompose_text(y_in_total + y_out_total + y_ct_total, m_in_total + m_out_total + m_ct_total, d_in_total + d_out_total + d_ct_total, ngay_vay_dt)})\n"
    
    # 8. XUẤT RA EXCEL
    excel_filename = "Bao_cao_dong_tien_kiem_sat.xlsx"
    os.makedirs("static", exist_ok=True)
    excel_filepath = os.path.join("static", excel_filename)
    
    excel_rows.extend([
        {"Hạng mục": "--- KẾT QUẢ TỔNG HỢP THEO PHƯƠNG PHÁP PHÂN TÁCH NĂM - THÁNG - NGÀY ---", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""},
        {"Hạng mục": "LÃI TRONG HẠN - Phần năm", "Nội dung chi tiết": f"{y_in_total:02d} năm", "Giá trị (VNĐ)": f"{i_y_in:,.0f}"},
        {"Hạng mục": "LÃI TRONG HẠN - Phần tháng", "Nội dung chi tiết": f"{m_in_total:02d} tháng", "Giá trị (VNĐ)": f"{i_m_in:,.0f}"},
        {"Hạng mục": "LÃI TRONG HẠN - Phần ngày", "Nội dung chi tiết": f"{d_in_total:02d} ngày", "Giá trị (VNĐ)": f"{i_d_in:,.0f}"},
        {"Hạng mục": "→ Tổng lãi trong hạn tồn đọng", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{lai_trong_han_chua_tra:,.0f}"},
        {"Hạng mục": "", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""},
        {"Hạng mục": "LÃI QUÁ HẠN - Phần năm", "Nội dung chi tiết": f"{y_out_total:02d} năm", "Giá trị (VNĐ)": f"{i_y_out:,.0f}"},
        {"Hạng mục": "LÃI QUÁ HẠN - Phần tháng", "Nội dung chi tiết": f"{m_out_total:02d} tháng", "Giá trị (VNĐ)": f"{i_m_out:,.0f}"},
        {"Hạng mục": "LÃI QUÁ HẠN - Phần ngày", "Nội dung chi tiết": f"{d_out_total:02d} ngày", "Giá trị (VNĐ)": f"{i_d_out:,.0f}"},
        {"Hạng mục": "→ Tổng lãi quá hạn tích lũy", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{tong_lai_qua_han_tich_luy:,.0f}"},
        {"Hạng mục": "", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""},
        {"Hạng mục": "LÃI CHẬM TRẢ - Phần năm", "Nội dung chi tiết": f"{y_ct_total:02d} năm", "Giá trị (VNĐ)": f"{i_y_ct:,.0f}"},
        {"Hạng mục": "LÃI CHẬM TRẢ - Phần tháng", "Nội dung chi tiết": f"{m_ct_total:02d} tháng", "Giá trị (VNĐ)": f"{i_m_ct:,.0f}"},
        {"Hạng mục": "LÃI CHẬM TRẢ - Phần ngày", "Nội dung chi tiết": f"{d_ct_total:02d} ngày", "Giá trị (VNĐ)": f"{i_d_ct:,.0f}"},
        {"Hạng mục": "→ Tổng lãi chậm trả tích lũy", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{tong_lai_cham_tra_tich_luy:,.0f}"},
        {"Hạng mục": "", "Nội dung chi tiết": "", "Giá trị (VNĐ)": ""},
        {"Hạng mục": "1. Dư nợ gốc còn lại (Đã đối trừ)", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{du_no_goc_hien_tai:,.0f}"},
        {"Hạng mục": "2. Lãi trong hạn tồn đọng", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{lai_trong_han_chua_tra:,.0f}"},
        {"Hạng mục": "3. Lãi quá hạn tích lũy (trên gốc)", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{tong_lai_qua_han_tich_luy:,.0f}"},
        {"Hạng mục": "4. Lãi chậm trả tích lũy (trên lãi)", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{tong_lai_cham_tra_tich_luy:,.0f}"},
        {"Hạng mục": "TỔNG CỘNG NGHĨA VỤ TÀI CHÍNH CHỐT SAU ĐỐI TRỪ", "Nội dung chi tiết": "", "Giá trị (VNĐ)": f"{tong_cong_nghia_vu:,.0f}"}
    ])
    
    pd.DataFrame(excel_rows).to_excel(excel_filepath, index=False)
    
    # 9. TÍNH BẢNG MA TRẬN HIỂN THỊ
    he_so_nam = max(1, total_days_simulation) / 365.0
    he_so_thang = max(1, total_days_simulation) / 30.4167
    
    matrix_data = {
        "goc": {"thang": du_no_goc_hien_tai / he_so_thang, "nam": du_no_goc_hien_tai / he_so_nam, "tong": du_no_goc_hien_tai},
        "lth": {"thang": lai_trong_han_chua_tra / he_so_thang, "nam": lai_trong_han_chua_tra / he_so_nam, "tong": lai_trong_han_chua_tra},
        "lqh": {"thang": tong_lai_qua_han_tich_luy / he_so_thang, "nam": tong_lai_qua_han_tich_luy / he_so_nam, "tong": tong_lai_qua_han_tich_luy},
        "lct": {"thang": tong_lai_cham_tra_tich_luy / he_so_thang, "nam": tong_lai_cham_tra_tich_luy / he_so_nam, "tong": tong_lai_cham_tra_tich_luy},
        "tong": {"thang": tong_cong_nghia_vu / he_so_thang, "nam": tong_cong_nghia_vu / he_so_nam, "tong": tong_cong_nghia_vu}
    }
    
    # Thông tin phân tách thời hạn để hiển thị ở frontend
    decomposed_info = {
        "tong_y": tong_y,
        "tong_m": tong_m, 
        "tong_d": tong_d,
        "decompose_text": format_decompose_text(tong_y, tong_m, tong_d, ngay_vay_dt),
        # Phân tách lãi trong hạn
        "lth_y": chi_tiet_trong_han['years'][0],
        "lth_m": chi_tiet_trong_han['months'][0],
        "lth_d": chi_tiet_trong_han['days'][0],
        "lth_interest_y": chi_tiet_trong_han['years'][1],
        "lth_interest_m": chi_tiet_trong_han['months'][1],
        "lth_interest_d": chi_tiet_trong_han['days'][1],
        # Phân tách lãi quá hạn
        "lqh_y": chi_tiet_qua_han['years'][0],
        "lqh_m": chi_tiet_qua_han['months'][0],
        "lqh_d": chi_tiet_qua_han['days'][0],
        "lqh_interest_y": chi_tiet_qua_han['years'][1],
        "lqh_interest_m": chi_tiet_qua_han['months'][1],
        "lqh_interest_d": chi_tiet_qua_han['days'][1],
        # Phân tách lãi chậm trả
        "lct_y": chi_tiet_cham_tra['years'][0],
        "lct_m": chi_tiet_cham_tra['months'][0],
        "lct_d": chi_tiet_cham_tra['days'][0],
        "lct_interest_y": chi_tiet_cham_tra['years'][1],
        "lct_interest_m": chi_tiet_cham_tra['months'][1],
        "lct_interest_d": chi_tiet_cham_tra['days'][1],
    }
    
    return {
        "matrix": matrix_data,
        "excel_url": f"/static/{excel_filename}",
        "so_ngay_thuc_te": total_days_simulation,
        "dien_giai": dien_giai_text,
        "decomposed": decomposed_info
    }


def _merge_detail(d1, d2):
    """Gộp 2 chi tiết phân tách."""
    return {
        'years': (d1['years'][0] + d2['years'][0], d1['years'][1] + d2['years'][1]),
        'months': (d1['months'][0] + d2['months'][0], d1['months'][1] + d2['months'][1]),
        'days': (d1['days'][0] + d2['days'][0], d1['days'][1] + d2['days'][1]),
    }