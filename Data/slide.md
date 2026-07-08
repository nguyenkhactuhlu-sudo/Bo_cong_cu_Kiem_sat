1. Hướng dẫn quy trình 4 bước sử dụng AI để tóm tắt nội dung vụ án/ vụ việc thành sơ đồ tư duy, định dạng Xmind  trực quan chỉ trong 2 phút.

2. BƯỚC 1: TẢI FILE

Tải Nội Dung Lên Gemini (hoặc Claude hoặc Chat GPT.v.v.)

Truy cập Gemini, nhấn biểu tượng kẹp giấy để tải file hồ sơ (Word/PDF). Hoặc copy-paste nội dung vụ án/ vụ việc đã che thông tin cá nhân hoặc các thông tin liên quan đến bảo mật của tài liệu.

BƯỚC 2: PROMPT

Yêu Cầu Tạo Mã Markdown

Gợi ý về câu lệnh yêu cầu AI tạo file có định dạng Markdown như sau:

Vụ án Hình sự (Phân tích cấu thành tội phạm)

Prompt: Hãy đóng vai là một Kiểm sát viên ngành Kiểm sát nhân dân, phân tích vụ án hình sự mà tôi tải lên và xuất ra kết quả dưới dạng mã Markdown (Markdown code block) để tôi import thẳng vào Xmind. Cấu trúc cây thư mục cần phân cấp rõ ràng bằng các tiêu đề (#, ##, ###): Tên vụ án; 1. Diễn biến tóm tắt; 2. Bốn yếu tố cấu thành tội phạm (Khách thể, Mặt khách quan, Chủ thể, Mặt chủ quan); 3. Định khung hình phạt và Tình tiết tăng nặng/giảm nhẹ; 4. Hướng giải quyết/ đề xuất. Lưu ý: Chỉ viết nội dung tóm tắt, ngắn gọn bằng từ khóa để Xmind hiển thị đẹp mắt, không viết đoạn văn dài.

Vụ án hình sự (Dành cho vụ án có diễn biến phức tạp, nhiều mốc thời gian (Trộm cắp, Giết người, Cướp tài sản...))

Prompt: Hãy đóng vai là một Kiểm sát viên ngành Kiểm sát nhân dân. Tôi có một vụ án hình sự với các dữ liệu thô từ file tải lên. Hãy sắp xếp và mô tả lại diễn biến sự việc này dưới dạng mã Markdown (Markdown code block) để tôi import vào Xmind làm sơ đồ tư duy. Cấu trúc cây thư mục yêu cầu phân cấp như sau: DIỄN BIẾN VỤ ÁN: [Tên vụ án]; 1. Giai đoạn chuẩn bị phạm tội (Thời gian, địa điểm, bàn bạc, chuẩn bị công cụ/phương tiện); 2. Giai đoạn thực hiện hành vi (Chuỗi hành động theo mốc thời gian chi tiết hh:mm - ngày/tháng); 3. Giai đoạn sau khi phạm tội (Che giấu dấu vết, tẩu tán tài sản, bỏ trốn); 4. Thời điểm bị phát hiện/bắt giữ. Lưu ý: Nội dung trong các nhánh phải cực kỳ ngắn gọn, sử dụng từ khóa hành động (ví dụ: "23:00 - Cậy cửa sau", "23:15 - Lấy 2 laptop"), không viết thành đoạn văn dài.

Vụ án hình sự (Dành cho vụ án có đồng phạm (Nhiều bị can, cần bóc tách hành vi từng người)

Prompt: Tôi cần lập sơ đồ tư duy Xmind để làm rõ diễn biến hành vi của từng đồng phạm trong vụ án: [Tên vụ án, ví dụ: Vụ án Cố ý gây thương tích tại quán karaoke X].

Hãy tạo một file Markdown tương thích với Xmind, sử dụng các dấu gạch đầu dòng - và thụt lề để phân nhánh. Sơ đồ cần tập trung vào việc tái hiện diễn biến theo vai trò: Nguyên nhân/Ngòi nổ sự việc: (Ai mâu thuẫn với ai? Vì lý do gì? Ở đâu?); Diễn biến hành vi của Bị can A (Chủ mưu): (Hô hào, kích động, cung cấp hung khí thế nào?); Diễn biến hành vi của Bị can B (Thực hành): (Trực tiếp tấn công ai? Gây thương tích vùng nào?); Diễn biến hành vi của các Đối tượng liên quan: (Can ngăn hay giúp sức bỏ trốn?); Hậu quả sự việc: (Tỷ lệ thương tích, thiệt hại tài sản). Xuất kết quả duy nhất trong khối mã Markdown để tôi copy-paste.

Vụ án hình sự (Dành cho vụ án Kinh tế / Chức vụ (Diễn biến là một chuỗi các giao dịch, thủ đoạn tinh vi))

Prompt: Hãy đóng vai Kiểm sát viên lập cáo trạng. Hãy chuyển hóa diễn biến hành vi phạm tội của vụ án kinh tế [Ví dụ: Vụ án Lừa đảo chiếm đoạt tài sản qua mạng của Nguyễn Văn A] thành mã Markdown chuẩn Xmind. Tập trung mô tả diễn biến theo Thủ đoạn và Dòng tiền: Diễn biến hành vi phạm tội - Bị can [Tên]; Bước 1: Tiếp cận & Tạo lòng tin (Lập tài khẩu ảo, đưa thông tin giả, hứa hẹn lợi nhuận...); Bước 2: Thao túng & Nhận tiền (Cách thức yêu cầu chuyển tiền, số tiền các mốc thời gian...); Bước 3: Xóa dấu vết & Chiếm đoạt (Cắt liên lạc, chuyển tiền qua nhiều tài khoản rác...); Bước 4: Chuỗi chứng cứ chứng minh hành vi (Dữ liệu điện tử, sao kê ngân hàng, lời khai người làm chứng...). Hãy tóm tắt thật cô đọng dưới dạng từ khóa trực quan để Xmind hiển thị đẹp nhất.

Vụ án Dân sự

Prompt: Hãy đóng vai là một trợ lý ảo cho Kiểm sát viên ngành Kiểm sát nhân dân. Tôi cần lập sơ đồ tư duy cho một vụ án dân sự về [Tranh chấp ……………]. Hãy tạo một file Markdown tương thích hoàn toàn với Xmind. Sử dụng dấu gạch đầu dòng - và thụt lề (Tab) để phân cấp các nhánh: Nhánh chính là "Thông tin chung", "Yêu cầu của nguyên đơn", "Ý kiến của bị đơn", "Tài liệu chứng cứ hiện có", và "Phương án hòa giải/Khởi kiện". Hãy tóm tắt các luận điểm cốt lõi dưới dạng từ khóa. Trả kết quả trong khối mã Markdown.

Vụ án Hành chính (Khiếu kiện quyết định xử phạt)

Prompt: Hãy viết một bản phân tích vụ án hành chính dưới dạng mã Markdown để nhập vào Xmind. Vụ việc: [Khiếu kiện Quyết định xử phạt vi phạm hành chính về …………….. của ……………………]. Sơ đồ tư duy cần có các nhánh chính: Đối tượng khởi kiện (Số quyết định, ngày ban hành, cơ quan ban hành); Thời hiệu khởi kiện; Tính hợp pháp về thẩm quyền và thủ tục ban hành; Tính hợp pháp về nội dung xử phạt; Đánh giá rủi ro và Đề xuất giải pháp. Xuất câu trả lời duy nhất trong khối mã Markdown.

Vụ án Kinh doanh Thương mại (Tranh chấp hợp đồng mua bán)

Prompt: Tạo cấu trúc Markdown để làm bản đồ tư duy Xmind phân tích vụ tranh chấp kinh doanh thương mại: [Tranh chấp hợp đồng cung ứng linh kiện giữa công ty A và công ty B]. Yêu cầu phân cấp bằng tiêu đề Markdown: Tranh chấp HĐTM [Tên vụ việc]; Tình trạng hợp đồng & Nghĩa vụ các bên; Vi phạm được viện dẫn (Bên A vi phạm gì, Bên B vi phạm gì); Giá trị tranh chấp & Cơ sở phạt vi phạm, bồi thường thiệt hại; Thẩm quyền giải quyết (Tòa án hay Trọng tài thương mại); Tài liệu cần bổ sung. Giữ các nội dung ở dạng gạch đầu dòng ngắn gọn.

Vụ án Lao động (Sa thải trái pháp luật)

Prompt: Bạn là một chuyên gia Pháp lý lao động. Hãy tạo file Markdown (tương thích Xmind) tóm tắt vụ án lao động: [Người lao động khiếu kiện Công ty X vì sa thải trái pháp luật]. Sơ đồ cần làm rõ: Quy trình xử lý kỷ luật của công ty có đúng luật không? Nghĩa vụ chứng minh của người sử dụng lao động? Các khoản bồi thường yêu cầu (Lương trong những ngày không được làm việc, trợ cấp, bồi thường tổn thất...). Viết ngắn gọn, trực quan, đặt trong khối mã để dễ sao chép.

Vụ việc Hôn nhân và Gia đình (Ly hôn, chia tài sản, giành quyền nuôi con)

Prompt: Hãy soạn một đoạn mã Markdown chuẩn Xmind để lập bản đồ tư duy cho vụ việc Hôn nhân gia đình: [Ly hôn và tranh chấp tài sản, quyền nuôi con giữa ông M và bà N]. Cấu trúc phân nhánh gồm: Quan hệ hôn nhân (Thời gian kết hôn, mâu thuẫn cốt lõi); Quyền nuôi con (Số lượng con, độ tuổi, nguyện vọng của con, điều kiện nuôi dưỡng của bố/mẹ); Tài tài chung & Nợ chung (Danh mục tài sản, nguồn gốc, đề xuất phân chia).

Vụ việc Sở hữu Trí tuệ (Tranh chấp nhãn hiệu/bản quyền)

Prompt: Hãy phân tích vụ việc [Tranh chấp hành vi xâm phạm nhãn hiệu độc quyền giữa thương hiệu X và Y] dưới dạng sơ đồ tư duy Markdown cho Xmind. Các nhánh lớn bao gồm: Chứng cứ chứng minh quyền sở hữu của nguyên đơn; Hành vi cấu thành xâm phạm của bị đơn (Yếu tố trùng/tương tự gây nhầm lẫn); Biện pháp xử lý đề xuất (Dân sự, hành chính hay hình sự); và Yêu cầu bồi thường thiệt hại.

Vụ việc Phá sản doanh nghiệp (Đánh giá tình trạng và thủ tục)

Prompt: Tạo một file Markdown tương thích với Xmind để quản lý quy trình [Tư vấn thủ tục phá sản cho Công ty Cổ phần X]. Phân cấp sơ đồ tư duy thành các bước: Đánh giá dấu hiệu mất khả năng thanh toán; Xác định các chủ nợ (Nợ có bảo đảm, nợ bảo đảm một phần, nợ không bảo đảm); Người có quyền nộp đơn; và Các bước xử lý tại Tòa án. Sử dụng cấu trúc # và ## rõ ràng.

Vụ việc Đầu tư/Dự án (Rà soát pháp lý - Legal Due Diligence)

Prompt: Hãy đóng vai chuyên gia tư vấn M&A. Tạo file Markdown dùng cho Xmind để phác thảo sơ đồ rà soát pháp lý rủi ro cho [Dự án bất động sản của Công ty Z]. Sơ đồ tư duy cần các nhánh: Tư cách pháp lý doanh nghiệp; Tình trạng pháp lý của đất dự án; Giấy phép xây dựng và quy hoạch; Các cam kết tài chính/thế chấp ngân hàng; và Kết luận (Mua/Không mua/Điều kiện kèm theo).

File Tổng hợp (Theo dõi tiến trình tố tụng của mọi vụ án)

Prompt: Hãy tạo một template Markdown đa dụng tương thích Xmind để theo dõi tiến trình tố tụng của một vụ án bất kỳ từ giai đoạn chuẩn bị đến thi hành án. Cấu trúc gồm:

Giai đoạn 1: Tiếp nhận & Đánh giá hồ sơ (Thời hiệu, thẩm quyền, chứng cứ).

Giai đoạn 2: Giai đoạn Sơ thẩm (Thủ tục thụ lý, hòa giải/giao nộp chứng cứ, phiên tòa).

Giai đoạn 3: Giai đoạn Phúc thẩm (nếu có).

Giai đoạn 4: Thi hành án. Trả kết quả dưới dạng khối mã Markdown từ khóa.

3. BƯỚC 3: LƯU TỆP

Lưu File Đuôi .md Với Notepad

Dán mã vào Notepad. Khi lưu, tại ô 'Save as type' chọn All Files (*.*) và đặt tên file là sodo.md. Chọn Encoding UTF-8 để không lỗi font.

4. BƯỚC 4: HOÀN TẤT

Nhập Vào Xmind

Mở Xmind, chọn File -> Import -> Markdown. Chọn file .md vừa lưu. Sơ đồ sẽ tự động bung nở với đầy đủ cấu trúc logic đã phân tích.