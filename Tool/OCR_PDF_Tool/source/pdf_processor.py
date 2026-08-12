"""
PDF Processor Module - Chuyển đổi PDF thành ảnh
Sử dụng PyMuPDF (fitz) để render từng trang PDF thành ảnh PNG.
"""

import os
import uuid
import fitz  # PyMuPDF

from config import PDF_RENDER_DPI, IMAGE_FORMAT, TEMP_DIR, ensure_dirs


class PDFProcessor:
    """Xử lý file PDF: mở, đếm trang, render thành ảnh."""

    def __init__(self, pdf_path: str):
        """
        Khởi tạo PDF Processor.

        Args:
            pdf_path: Đường dẫn đến file PDF
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Không tìm thấy file PDF: {pdf_path}")

        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.total_pages = len(self.doc)
        # Generate ASCII-safe prefix for temp image filenames
        # (Tesseract subprocess can't handle Unicode paths on Windows)
        self._img_prefix = str(uuid.uuid4())[:8]

    def get_page_count(self) -> int:
        """Trả về tổng số trang của PDF."""
        return self.total_pages

    def get_file_name(self) -> str:
        """Trả về tên file (không có đuôi mở rộng)."""
        return os.path.splitext(os.path.basename(self.pdf_path))[0]

    def render_page(self, page_num: int, output_dir: str = None) -> str:
        """
        Render một trang PDF thành ảnh PNG.

        Args:
            page_num: Số thứ tự trang (0-indexed)
            output_dir: Thư mục lưu ảnh (mặc định: TEMP_DIR)

        Returns:
            Đường dẫn đến file ảnh đã tạo

        Raises:
            ValueError: Nếu số trang không hợp lệ
        """
        if page_num < 0 or page_num >= self.total_pages:
            raise ValueError(
                f"Số trang không hợp lệ: {page_num + 1}. "
                f"PDF có {self.total_pages} trang (1-{self.total_pages})."
            )

        if output_dir is None:
            output_dir = TEMP_DIR

        ensure_dirs()

        # Render trang với DPI cao
        page = self.doc[page_num]
        # Ma trận zoom để đạt DPI mong muốn
        zoom = PDF_RENDER_DPI / 72.0  # 72 DPI là mặc định của PDF
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, dpi=PDF_RENDER_DPI)

        # Tạo tên file ảnh (ASCII-safe — Tesseract không xử lý được Unicode path)
        image_filename = f"{self._img_prefix}_page_{page_num + 1:04d}.{IMAGE_FORMAT}"
        image_path = os.path.join(output_dir, image_filename)

        # Lưu ảnh
        pix.save(image_path)

        return image_path

    def render_all_pages(self, output_dir: str = None) -> list:
        """
        Render tất cả các trang PDF thành ảnh.

        Args:
            output_dir: Thư mục lưu ảnh

        Returns:
            Danh sách đường dẫn đến các file ảnh
        """
        image_paths = []
        for page_num in range(self.total_pages):
            img_path = self.render_page(page_num, output_dir)
            image_paths.append(img_path)
        return image_paths

    def close(self):
        """Đóng file PDF."""
        if self.doc:
            self.doc.close()