"""Chuyển Word .doc cũ sang .docx bằng Microsoft Word COM trên Windows."""

from __future__ import annotations

from pathlib import Path


class DocConversionError(RuntimeError):
    """Lỗi chuyển đổi có thông báo phù hợp để hiển thị cho người dùng."""


def convert_doc_to_docx(source: str | Path, destination: str | Path) -> Path:
    """Chuyển ``source.doc`` sang ``destination.docx`` mà không sửa tệp gốc."""
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()
    if source_path.suffix.casefold() != ".doc":
        raise ValueError("Tệp nguồn phải có định dạng .doc.")
    if destination_path.suffix.casefold() != ".docx":
        raise ValueError("Tệp đích phải có định dạng .docx.")
    if not source_path.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp: {source_path.name}")

    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise DocConversionError(
            "Bản công cụ hiện tại thiếu thành phần chuyển đổi tệp .doc. "
            "Vui lòng tải lại bản mới nhất."
        ) from exc

    word = None
    document = None
    com_initialized = False
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.unlink(missing_ok=True)
    try:
        pythoncom.CoInitialize()
        com_initialized = True
        # DispatchEx tạo phiên Word riêng, không can thiệp tài liệu Word người dùng đang mở.
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        try:
            # msoAutomationSecurityForceDisable: không chạy macro chứa trong tệp .doc.
            word.AutomationSecurity = 3
        except Exception:
            pass
        document = word.Documents.Open(
            str(source_path), ReadOnly=True, AddToRecentFiles=False,
            ConfirmConversions=False, NoEncodingDialog=True,
        )
        document.SaveAs2(str(destination_path), FileFormat=16)
        document.Close(SaveChanges=False)
        document = None
        if not destination_path.exists():
            raise DocConversionError("Microsoft Word không tạo được tệp .docx tạm.")
        return destination_path
    except DocConversionError:
        raise
    except Exception as exc:
        destination_path.unlink(missing_ok=True)
        raise DocConversionError(
            "Không thể chuyển tệp .doc sang .docx. Máy cần cài Microsoft Word; "
            "hãy đóng các hộp thoại Word đang mở rồi thử lại. "
            f"Chi tiết: {exc}"
        ) from exc
    finally:
        if document is not None:
            try:
                document.Close(SaveChanges=False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        if com_initialized:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
