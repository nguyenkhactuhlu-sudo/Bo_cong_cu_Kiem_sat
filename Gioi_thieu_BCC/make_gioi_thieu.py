# -*- coding: utf-8 -*-
"""Sinh file Word giới thiệu tính năng Bộ công cụ nghiệp vụ Kiểm sát (BCCVKS).
Tập trung giới thiệu tính năng; không bìa.
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def set_cell_bg(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)


def add_para(doc, text, bold=False, size=13, align=None, space_after=6, italic=False, color=None):
    p = doc.add_paragraph()
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = 'Times New Roman'
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    return p


def add_heading(doc, text, size=15, color='1F4E79', space_before=10, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    run.font.name = 'Times New Roman'
    return p


def add_bullet(doc, text, size=13):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.name = 'Times New Roman'
    return p


def add_table(doc, headers, rows, col_widths=None, header_fill='1F4E79'):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ''
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r.font.name = 'Times New Roman'
        set_cell_bg(hdr[i], header_fill)
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ''
            p = cells[i].paragraphs[0]
            r = p.add_run(str(val))
            r.font.size = Pt(12)
            r.font.name = 'Times New Roman'
            if i == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if col_widths:
        for i, w in enumerate(col_widths):
            for cell in table.columns[i].cells:
                cell.width = Cm(w)
    return table


def main():
    doc = Document()

    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.0)

    # --- Tiêu đề ---
    add_para(doc, 'BỘ CÔNG CỤ NGHIỆP VỤ KIỂM SÁT (BCCVKS)',
             bold=True, size=18, align=WD_ALIGN_PARAGRAPH.CENTER, color='1F4E79', space_after=2)
    add_para(doc, 'GIỚI THIỆU TÍNH NĂNG',
             bold=True, size=15, align=WD_ALIGN_PARAGRAPH.CENTER, color='C00000', space_after=12)

    # --- Mở đầu ---
    add_para(doc,
        'BCCVKS là bộ công cụ tổng hợp hỗ trợ Kiểm sát viên (KSV), Kiểm tra viên, Chuyên viên xử lý '
        'công việc nghiệp vụ hàng ngày: tính toán nghiệp vụ, xử lý văn bản, tài liệu và tra cứu pháp '
        'luật. Bộ công cụ gồm 02 nhóm:')
    add_bullet(doc, 'Nhóm Offline (07 công cụ): tải về và chạy hoàn toàn trên máy tính, '
                    'không cần kết nối mạng (kể cả máy Quản lý án hình sự); dữ liệu văn bản, hồ sơ '
                    'không rời khỏi máy tính, bảo đảm an toàn tuyệt đối.')
    add_bullet(doc, 'Nhóm cần kết nối mạng (05 công cụ): sử dụng dịch vụ AI (Udify, NotebookLM, Gemini) '
                    'để hỗ trợ kiểm sát bản án, tra cứu pháp luật và xử lý thông báo thụ lý vụ án.')

    # ===== NHÓM OFFLINE =====
    add_heading(doc, 'I. NHÓM CÔNG CỤ OFFLINE (7 công cụ)')
    add_para(doc, 'Tải về và cài đặt một lần; chạy hoàn toàn trên máy tính không kết nối mạng, '
                  'phục vụ xử lý văn bản, tài liệu của KSV.', italic=True, space_after=8)

    add_para(doc, '1. Tự động tính tiền lãi', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Tự động tính tiền lãi trong hạn, lãi quá hạn, lãi chậm trả trong giao dịch dân sự theo Nghị quyết 01/2019/NQ-HĐTP; nhập số gốc, thời gian, lãi suất cho kết quả chính xác trong giây lát.')

    add_para(doc, '2. Tính án phí', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Tra cứu, tự động tính nhanh số tiền án phí hình sự và dân sự theo Pháp lệnh án phí, lệ phí Tòa án.')

    add_para(doc, '3. Tính tuổi — Tính thời hạn — Tạm giữ, tạm giam', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Tính tuổi, ngày/tháng/năm, giờ/phút của đối tượng.')
    add_bullet(doc, 'Tính thời hạn tạm giữ theo giờ, có cảnh báo đỏ/vàng theo Điều 117, 118 BLTTHS.')
    add_bullet(doc, 'Tính thời hạn tạm giam theo Điều 17 Thông tư liên tịch 04/2018 (1 tháng = 30 ngày, tính liên tục cả ngày nghỉ, tự trừ số ngày đã tạm giữ), cảnh báo khi sắp hết hạn.')
    add_bullet(doc, 'Tính thời hạn tố tụng theo Điều 134, 135 BLTTHS, tự động dời ngày nghỉ khi ngày cuối rơi vào thứ Bảy, Chủ nhật, ngày lễ.')

    add_para(doc, '4. Tự động che thông tin', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Tự động ẩn (che) toàn bộ thông tin cá nhân trong văn bản Word (tên, địa chỉ, số điện thoại…) trước khi công bố hoặc giao cho AI xử lý; nhanh chóng, không bỏ sót.')

    add_para(doc, '5. Tự động đổi tên file', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Đổi tên file hàng loạt: quét toàn bộ thư mục con, xem trước trước khi thực hiện, chuẩn hóa Unicode, thêm tiền tố/hậu tố, đánh số thứ tự bút lục, tài liệu, rút gọn tên văn bản pháp luật.')

    add_para(doc, '6. Rà soát chính tả văn bản Word', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Tự động phát hiện lỗi chính tả, cụm từ nghiệp vụ, khoảng trắng, dấu câu trong văn bản Word; xuất bản Word tô vàng các vị trí cần kiểm tra hoặc bản đã sửa. Chạy offline, không gửi dữ liệu lên mạng.')

    add_para(doc, '7. Nhận dạng chữ trong PDF, ảnh (OCR)', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Tự động trích xuất chữ từ file PDF (kể cả PDF scan) và file ảnh (JPG, PNG, TIFF…) bằng Tesseract OCR offline; xuất kết quả ra Word, Markdown hoặc TXT; hỗ trợ xử lý một hoặc nhiều file.')

    # ===== NHÓM CẦN MẠNG =====
    add_heading(doc, 'II. NHÓM CÔNG CỤ CẦN KẾT NỐI MẠNG (5 công cụ)')
    add_para(doc, 'Cần kết nối Internet, sử dụng dịch vụ AI bên ngoài để hỗ trợ nghiệp vụ.', italic=True, space_after=8)

    add_para(doc, '1. Kiểm sát bản án — Bản dùng chung', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Đối chiếu, tự động phát hiện lỗi chính tả, mâu thuẫn, vi phạm, thiếu sót trong bản án hình sự, dân sự; dùng chung, miễn phí cho các đơn vị.')

    add_para(doc, '2. Kiểm sát bản án — Bản chuyên biệt', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Bản nâng cấp tối ưu riêng cho Viện KSND KV5 Bắc Ninh.')

    add_para(doc, '3. Hình sự & Tố tụng hình sự (NotebookLM)', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Tra cứu điều luật, hỗ trợ lập luận tố tụng dựa trên kho tri thức pháp luật hiện hành.')

    add_para(doc, '4. Hướng dẫn tạo sơ đồ tư duy', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Hướng dẫn thao tác chi tiết và bộ prompt mẫu để tạo sơ đồ tư duy tự động bằng AI.')

    add_para(doc, '5. Quản lý thông báo thụ lý vụ án', bold=True, size=13, space_after=2)
    add_bullet(doc, 'Tự động đọc PDF scan, nhận diện thông tin vụ án và đương sự bằng Gemini; hỗ trợ quản lý hồ sơ, ghi sổ Excel và soạn thảo văn bản kiểm sát theo mẫu.')

    # ===== ĐIỂM NỔI BẬT =====
    add_heading(doc, 'III. ĐIỂM NỔI BẬT')
    add_bullet(doc, 'Chạy hoàn toàn offline (nhóm Offline), không gửi văn bản, hồ sơ vụ án ra ngoài → an toàn dữ liệu tuyệt đối, sử dụng được cả trên máy Quản lý án hình sự.')
    add_bullet(doc, 'Mỗi công cụ được xây dựng theo đúng căn cứ pháp lý cụ thể, kết quả chính xác, kèm cơ sở pháp lý.')
    add_bullet(doc, 'Miễn phí, mã nguồn mở, không chi phí bản quyền hay duy trì.')
    add_bullet(doc, 'Dễ triển khai: nhóm Offline cài một file duy nhất, không cần Python, trình duyệt hay Internet.')

    out_path = 'Gioi_thieu_BCC/Gioi_thieu_BCCVKS.docx'
    doc.save(out_path)
    print('OK - Created:', out_path)


if __name__ == '__main__':
    main()