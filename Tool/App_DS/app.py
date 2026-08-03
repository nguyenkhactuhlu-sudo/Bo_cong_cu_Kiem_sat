from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/tinh', methods=['POST'])
def tinh():
    try:
        gia_tri = float(request.form.get('gia_tri', 0))
        loai_phi = request.form.get('loai_phi')
        giam_50 = request.form.get('giam_50')  # 'on' nếu checkbox được tích, None nếu không
        
        cong_thuc = ""
        ket_qua = 0

        # 1. Logic tính cho Lao động (Đúng theo quy định bạn cung cấp)
        if loai_phi == 'lao_dong_co_gia_ngach':
            if gia_tri <= 6000000:
                ket_qua, cong_thuc = 300000, "Mức cố định: 300.000 VNĐ"
            elif gia_tri <= 400000000:
                ket_qua = gia_tri * 0.03
                cong_thuc = f"{gia_tri:,.0f} x 3% (tối thiểu 300k)"
            elif gia_tri <= 2000000000:
                ket_qua = 12000000 + (gia_tri - 400000000) * 0.02
                cong_thuc = f"12tr + ({gia_tri:,.0f} - 400tr) x 2%"
            else: # Trên 2 tỷ
                ket_qua = 44000000 + (gia_tri - 2000000000) * 0.001
                cong_thuc = f"44tr + ({gia_tri:,.0f} - 2 tỷ) x 0.1%"
            
            # Đảm bảo sàn 300k cho Lao động
            ket_qua = max(300000, ket_qua)

        # 2. Logic cho Dân sự/KDTM (Giữ nguyên biểu mức cũ)
        else:
            if gia_tri <= 6000000:
                ket_qua, cong_thuc = 300000, "Mức cố định: 300.000 VNĐ"
            elif gia_tri <= 400000000:
                ket_qua, cong_thuc = gia_tri * 0.05, f"{gia_tri:,.0f} x 5%"
            elif gia_tri <= 800000000:
                ket_qua = 20000000 + (gia_tri - 400000000) * 0.04
                cong_thuc = f"20tr + ({gia_tri:,.0f} - 400tr) x 4%"
            elif gia_tri <= 2000000000:
                ket_qua = 36000000 + (gia_tri - 800000000) * 0.03
                cong_thuc = f"36tr + ({gia_tri:,.0f} - 800tr) x 3%"
            elif gia_tri <= 4000000000:
                ket_qua = 72000000 + (gia_tri - 2000000000) * 0.02
                cong_thuc = f"72tr + ({gia_tri:,.0f} - 2 tỷ) x 2%"
            else:
                ket_qua = 112000000 + (gia_tri - 4000000000) * 0.001
                cong_thuc = f"112tr + ({gia_tri:,.0f} - 4 tỷ) x 0.1%"
        
        # Lưu án phí gốc trước khi giảm
        ket_qua_goc = ket_qua
        giam_50_ap_dung = False
        so_giam = 0

        # 3. Áp dụng giảm 50% nếu checkbox được tích (Điều 27 NQ 326/2016)
        if giam_50 == 'on':
            so_giam = ket_qua * 0.5
            ket_qua = ket_qua * 0.5
            giam_50_ap_dung = True
            cong_thuc += " → Giảm 50% (Điều 27 NQ 326/2016)"
        
        return render_template('index.html', 
                               gia_tri_nhap=gia_tri, 
                               ket_qua="{:,.0f}".format(ket_qua),
                               ket_qua_goc="{:,.0f}".format(ket_qua_goc),
                               so_giam="{:,.0f}".format(so_giam),
                               giam_50_ap_dung=giam_50_ap_dung,
                               cong_thuc=cong_thuc)
    
    except (ValueError, TypeError):
        return render_template('index.html', ket_qua="Lỗi định dạng số!")

if __name__ == '__main__':
    app.run(debug=True)