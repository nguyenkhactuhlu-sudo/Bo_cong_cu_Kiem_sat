"""
OCR Engine Module - Wrapper cho Tesseract OCR
Gọi tesseract.exe qua subprocess để thực hiện OCR.
"""

import subprocess
import os

from config import TESSERACT_EXE, TESSDATA_DIR, TESSERACT_PSM, TESSERACT_OEM


class OCREngine:
    """Engine OCR sử dụng Tesseract portable."""

    def __init__(self, language: str = "vie"):
        """
        Khởi tạo OCR Engine.

        Args:
            language: Mã ngôn ngữ Tesseract (ví dụ: 'vie', 'vie+eng')
        """
        self.language = language
        self.tesseract_path = TESSERACT_EXE
        self.tessdata_path = TESSDATA_DIR
        self._validate_tesseract()

    def _validate_tesseract(self):
        """Kiểm tra Tesseract có tồn tại và hoạt động."""
        if not os.path.exists(self.tesseract_path):
            raise FileNotFoundError(
                f"Không tìm thấy Tesseract tại: {self.tesseract_path}\n"
                f"Vui lòng đảm bảo thư mục 'OCR\\Tesseract-OCR' tồn tại."
            )

        # Kiểm tra tesseract có chạy được không
        try:
            result = subprocess.run(
                [self.tesseract_path, "--version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                raise RuntimeError(f"Tesseract không hoạt động: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Tesseract không phản hồi (timeout).")
        except FileNotFoundError:
            raise FileNotFoundError(f"Không thể chạy: {self.tesseract_path}")

    def set_language(self, language: str):
        """Thay đổi ngôn ngữ OCR."""
        self.language = language

    def ocr_image(self, image_path: str, output_base: str) -> str:
        """
        Thực hiện OCR trên một file ảnh.

        Args:
            image_path: Đường dẫn đến file ảnh (PNG, JPEG, TIFF)
            output_base: Tên file output (không có đuôi mở rộng)

        Returns:
            Nội dung văn bản đã nhận dạng (chuỗi text)

        Raises:
            RuntimeError: Nếu OCR thất bại
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Không tìm thấy ảnh: {image_path}")

        # Lệnh: tesseract input_image output_base -l vie --psm 6 --oem 3 --tessdata-dir ...
        cmd = [
            self.tesseract_path,
            image_path,
            output_base,
            "-l", self.language,
            "--psm", str(TESSERACT_PSM),
            "--oem", str(TESSERACT_OEM),
            "--tessdata-dir", self.tessdata_path,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 phút timeout mỗi trang
                env={**os.environ, "TESSDATA_PREFIX": self.tessdata_path}
            )

            # Tesseract tạo file output_base.txt
            output_file = f"{output_base}.txt"

            if not os.path.exists(output_file):
                raise RuntimeError(
                    f"Tesseract không tạo file output.\n"
                    f"STDERR: {result.stderr}\n"
                    f"STDOUT: {result.stdout}"
                )

            with open(output_file, "r", encoding="utf-8") as f:
                text = f.read()

            # Dọn dẹp file output trung gian
            try:
                os.remove(output_file)
            except OSError:
                pass

            return text.strip()

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"OCR timeout (>120s) cho ảnh: {image_path}")
        except Exception as e:
            raise RuntimeError(f"Lỗi OCR: {str(e)}")

    def ocr_image_to_file(self, image_path: str, output_path: str) -> str:
        """
        Thực hiện OCR và ghi kết quả vào file.

        Args:
            image_path: Đường dẫn đến file ảnh
            output_path: Đường dẫn file output .txt

        Returns:
            Nội dung văn bản đã nhận dạng
        """
        text = self.ocr_image(image_path, output_path.replace(".txt", ""))

        # Ghi kết quả vào file chỉ định
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        return text