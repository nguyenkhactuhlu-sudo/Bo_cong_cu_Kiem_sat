"""Benchmark nhỏ, tái lập được cho engine không AI."""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import VietnameseSpellChecker


ERROR_CASES = [
    ("Viện kiểm xát nhân dân", "kiểm xát"),
    ("Kiểm xát viên nghiên cứu hồ sơ.", "Kiểm xát"),
    ("Quyết định khỏi tố bị can.", "khỏi tố"),
    ("Bị cao Nguyễn Văn A khai nhận.", "Bị cao"),
    ("Cơ quan điều tra đề nghị truy té.", "truy té"),
    ("Ban hành cáo chạng số 12.", "cáo chạng"),
    ("Thời hạn tạm dữ là ba ngày.", "tạm dữ"),
    ("Thẩm quyển giải quyết thuộc Tòa án.", "Thẩm quyển"),
    ("Kết luận điểu tra vụ án.", "điểu tra"),
    ("Xác định trách nhiêm hình sự.", "trách nhiêm"),
    ("Thực hiện đúng quy định pháp luât.", "pháp luât"),
    ("Danh mục vật chứn kèm theo.", "vật chứn"),
    ("Tài liệu tại bút lụt số 15.", "bút lụt"),
    ("Lập biên bãn giao nhận.", "biên bãn"),
    ("Quyền của đương sư được bảo đảm.", "đương sư"),
    ("Công tác thi hành áng dân sự.", "thi hành áng"),
    ("Viện kiểm sát  nhân dân.", "  "),
    ("Nội dung ,tài liệu kèm theo.", " ,"),
]

CLEAN_CASES = [
    "Viện kiểm sát nhân dân ban hành quyết định khởi tố bị can.",
    "Kiểm sát viên nghiên cứu hồ sơ vụ án.",
    "Bị cáo Nguyễn Văn A trình bày tại phiên tòa.",
    "Cơ quan điều tra đã chuyển kết luận điều tra.",
    "Thời hạn tạm giữ được tính theo giờ.",
    "VKSND khu vực thực hành quyền công tố và kiểm sát xét xử.",
    "Quyết định số 12/QĐ-VKS ngày 01/08/2026.",
    "Đương sự có quyền kháng cáo bản án sơ thẩm.",
    "Tài liệu được đánh số bút lục từ 01 đến 25.",
    "Hội đồng xét xử tuyên án công khai.",
]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    checker = VietnameseSpellChecker()
    started = time.perf_counter()
    caught = 0
    for text, target in ERROR_CASES:
        issues = checker.check_text(text)
        if any(target in issue.original for issue in issues):
            caught += 1
        else:
            print("BỎ SÓT:", text)
    false_positive = 0
    for text in CLEAN_CASES:
        issues = [issue for issue in checker.check_text(text) if issue.severity == "error"]
        if issues:
            false_positive += 1
            print("BÁO NHẦM:", text, [issue.original for issue in issues])
    elapsed = (time.perf_counter() - started) * 1000
    print(f"Bắt đúng: {caught}/{len(ERROR_CASES)}")
    print(f"Câu sạch bị báo lỗi chắc chắn: {false_positive}/{len(CLEAN_CASES)}")
    print(f"Thời gian: {elapsed:.1f} ms")
    return 0 if caught == len(ERROR_CASES) and false_positive == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
