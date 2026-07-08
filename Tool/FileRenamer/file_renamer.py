"""
File Renamer - Tự động đổi tên file thông minh (Standalone Version)
===================================================================
Module này cung cấp công cụ tự động nhận diện và đổi tên các file có:
- Tên quá dài (>60 ký tự)
- Tên tiếng Việt có dấu (dạng NFC/NFD phức tạp, khó xử lý)
- Tên chứa ký tự đặc biệt, khoảng trắng thừa
- Tên khó đọc, thiếu tính mô tả

Mục tiêu: Chuẩn hóa tên file để dễ xử lý trong quy trình RAG,
Miranki có thể gọi tool này để làm sạch workspace trước khi index.

Phiên bản standalone: Có thể chạy độc lập, không phụ thuộc vào
cấu trúc thư mục của dự án Deepseek Cowork.

Sử dụng dòng lệnh:
    python file_renamer.py --path D:\deepseek_workspace --dry-run
    python file_renamer.py --path D:\deepseek_workspace --execute
    python file_renamer.py --path D:\deepseek_workspace --subdir "Kho_tai_lieu" --dry-run
    python file_renamer.py --path D:\deepseek_workspace --file "Quyết định khởi tố.docx" --dry-run

Sử dụng như module Python:
    from file_renamer import FileRenamer
    renamer = FileRenamer()
    results = renamer.auto_rename_all("d:/workspace", dry_run=True)
    print(renamer.format_results(results, dry_run=True))
"""

import os
import re
import sys
import unicodedata
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

# ============================================================
# Cấu hình
# ============================================================

MAX_NAME_LENGTH = 60

VN_ABBREVIATIONS = {
    # Văn bản pháp quy
    "nghi dinh": "ND",
    "thong tu": "TT",
    "nghi quyet": "NQ",
    "quyet dinh": "QD",
    "chi thi": "CT",
    "hien phap": "HP",
    "bo luat": "BL",
    "luat": "L",
    "phap lenh": "PL",
    "van ban": "VB",
    "cong van": "CV",
    "thong bao": "TB",
    "huong dan": "HD",
    "quy che": "QC",
    "quy dinh": "QDinh",
    "dieu le": "DL",
    "tieu chuan": "TC",
    "quy chuan": "QChuan",
    "ke hoach": "KH",
    "bao cao": "BC",
    "to trinh": "TTr",
    "de an": "DA",
    "phuong an": "PA",
    "de nghi": "DN",
    "kien nghi": "KN",
    "khang nghi": "KNghi",
    "khieu nai": "KNai",
    "don": "Don",

    # Cơ quan, tổ chức
    "bo": "Bo",
    "so": "So",
    "vien kiem sat": "VKS",
    "toa an": "TA",
    "uy ban": "UB",
    "hoi dong": "HDong",
    "chinh phu": "CP",
    "quoc hoi": "QH",
    "thu tuong": "TTg",
    "bo truong": "BT",
    "chu tich": "CTich",
    "vien truong": "VT",
    "chanh an": "CA",
    "tong cuc": "TCuc",
    "cuc": "Cuc",
    "chi cuc": "CCuc",
    "phong": "P",
    "ban": "Ban",
    "doan": "Doan",
    "to": "To",
    "doi": "Doi",

    # Lĩnh vực pháp lý
    "hinh su": "HS",
    "dan su": "DS",
    "hanh chinh": "HC",
    "kinh te": "KT",
    "lao dong": "LD",
    "dat dai": "DD",
    "hon nhan": "HN",
    "gia dinh": "GD",
    "thuong mai": "TM",
    "so huu tri tue": "SHTT",
    "moi truong": "MT",
    "giao thong": "GT",
    "xay dung": "XD",
    "y te": "YT",
    "giao duc": "GDuc",
    "tai chinh": "TCinh",
    "ngan hang": "NH",

    # Từ khóa phổ biến
    "sua doi": "SD",
    "bo sung": "BS",
    "huong dan thi hanh": "HDTH",
    "thi hanh": "TH",
    "pho bien": "PB",
    "giao duc phap luat": "GDPL",
    "phap luat": "PLuat",
    "to tung": "TTung",
    "xu phat": "XP",
    "vi pham": "VP",
    "hanh chinh": "HC",
    "boi thuong": "BTg",
    "tranh chap": "TChap",
    "khoi to": "KTo",
    "truy to": "TTo",
    "xet xu": "XXu",
    "tam giam": "TGiam",
    "tam giu": "TGiu",
    "bat": "Bat",
    "kham xet": "KXet",
    "thu giu": "TGu",
    "phong toa": "PToa",
    "ke bien": "KBien",
    "hoa giai": "HGiai",
    "trong tai": "TTai",
    "phuc tham": "PTham",
    "so tham": "STham",
    "giam doc tham": "GDT",
    "tai tham": "TTam",

    # Khác
    "cong hoa xa hoi chu nghia viet nam": "CHXHCNVN",
    "doc lap tu do hanh phuc": "DLTDHP",
    "phu luc": "PL",
    "mau": "M",
    "bieu mau": "BM",
    "so": "So",
    "ngay": "",
    "thang": "",
    "nam": "",
}


@dataclass
class RenameResult:
    old_path: str
    new_path: str
    old_name: str
    new_name: str
    reason: str
    renamed: bool = False
    error: Optional[str] = None


@dataclass
class BatchRenameResult:
    total_scanned: int = 0
    total_problematic: int = 0
    total_renamed: int = 0
    total_skipped: int = 0
    total_errors: int = 0
    results: List[RenameResult] = field(default_factory=list)


class FileRenamer:

    def __init__(self, max_name_length: int = MAX_NAME_LENGTH):
        self.max_name_length = max_name_length
        self._vn_pattern = re.compile(
            r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]',
            re.IGNORECASE
        )
        self._special_chars_pattern = re.compile(r'[^\w\s\-\.\(\)\[\]_,&+]+')
        self._multi_space_pattern = re.compile(r'\s+')
        self._multi_underscore_pattern = re.compile(r'_{2,}')

    @staticmethod
    def normalize_unicode(text: str) -> str:
        return unicodedata.normalize('NFC', text)

    @staticmethod
    def remove_diacritics(text: str) -> str:
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        return text

    @staticmethod
    def clean_special_chars(text: str) -> str:
        text = re.sub(r'[^\w\s\-\.\(\)\[\]_,&+]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'-{2,}', '-', text)
        text = re.sub(r'_{2,}', '_', text)
        return text

    def abbreviate_text(self, text: str) -> str:
        sorted_abbrs = sorted(VN_ABBREVIATIONS.items(),
                              key=lambda x: len(x[0]), reverse=True)
        for full, abbr in sorted_abbrs:
            if not abbr:
                continue
            pattern = re.compile(r'\b' + re.escape(full) + r'\b', re.IGNORECASE)
            text = pattern.sub(abbr, text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def shorten_name(self, name_no_ext: str, max_len: int = None) -> str:
        if max_len is None:
            max_len = self.max_name_length
        if len(name_no_ext) <= max_len:
            return name_no_ext
        abbreviated = self.abbreviate_text(name_no_ext)
        if len(abbreviated) <= max_len:
            return abbreviated
        abbreviated = re.sub(r'\b(ngay|thang|nam)\s+\d+\b', '', abbreviated,
                             flags=re.IGNORECASE)
        abbreviated = re.sub(r'\s+', ' ', abbreviated).strip()
        if len(abbreviated) <= max_len:
            return abbreviated
        truncate_at = max_len - 2
        return abbreviated[:truncate_at].rstrip() + ".."

    def generate_clean_name(self, original_name: str) -> str:
        path_obj = Path(original_name)
        stem = path_obj.stem
        suffix = path_obj.suffix
        cleaned = self.normalize_unicode(stem)
        if self._vn_pattern.search(cleaned):
            cleaned = self.remove_diacritics(cleaned)
        cleaned = self.clean_special_chars(cleaned)
        cleaned = self.abbreviate_text(cleaned)
        cleaned = self.shorten_name(cleaned)
        if not cleaned:
            cleaned = "file"
        result = cleaned + suffix
        if len(result) > 100:
            available = 95 - len(suffix)
            if available > 5:
                cleaned = cleaned[:available].rstrip()
                result = cleaned + suffix
        return result

    def is_problematic_name(self, filename: str) -> Tuple[bool, List[str]]:
        name = Path(filename).name
        stem = Path(name).stem
        reasons = []
        if self._vn_pattern.search(stem):
            reasons.append("Ten co chua tieng Viet co dau")
        if len(stem) > self.max_name_length:
            reasons.append(f"Ten qua dai ({len(stem)} ky tu, toi da {self.max_name_length})")
        special = self._special_chars_pattern.findall(stem)
        if special:
            reasons.append(f"Ten chua ky tu dac biet: {', '.join(set(special[:3]))}")
        if self._multi_space_pattern.search(stem) and '  ' in stem:
            reasons.append("Ten co nhieu khoang trang lien tiep")
        if self._multi_underscore_pattern.search(stem):
            reasons.append("Ten co nhieu dau gach duoi lien tiep")
        return (len(reasons) > 0, reasons)

    def scan_workspace(self, workspace_path: str,
                       recursive: bool = True,
                       skip_dirs: Optional[List[str]] = None) -> List[str]:
        if skip_dirs is None:
            skip_dirs = ['.git', '__pycache__', '.vscode', 'node_modules',
                         'chroma_law_db', 'File_khong_loc_duoc']
        ws = Path(workspace_path).resolve()
        problematic_files = []
        iterator = ws.rglob("*") if recursive else ws.iterdir()
        for item in iterator:
            try:
                if not item.is_file():
                    continue
                parts = item.relative_to(ws).parts
                if any(part in skip_dirs for part in parts):
                    continue
                if item.name.startswith('.'):
                    continue
                is_problem, _ = self.is_problematic_name(item.name)
                if is_problem:
                    rel_path = str(item.relative_to(ws))
                    problematic_files.append(rel_path)
            except (PermissionError, OSError, ValueError):
                continue
        return problematic_files

    def rename_file(self, file_path: str, workspace_path: str,
                    dry_run: bool = True) -> RenameResult:
        ws = Path(workspace_path).resolve()
        full_path = ws / file_path
        if not full_path.exists():
            return RenameResult(
                old_path=file_path, new_path="",
                old_name=Path(file_path).name, new_name="",
                reason="", renamed=False,
                error=f"File khong ton tai: {file_path}"
            )
        old_name = full_path.name
        is_problem, reasons = self.is_problematic_name(old_name)
        if not is_problem:
            return RenameResult(
                old_path=file_path, new_path=file_path,
                old_name=old_name, new_name=old_name,
                reason="Ten file da on, khong can doi", renamed=False
            )
        new_name = self.generate_clean_name(old_name)
        if new_name == old_name:
            return RenameResult(
                old_path=file_path, new_path=file_path,
                old_name=old_name, new_name=new_name,
                reason="Ten sau khi chuan hoa giong ten cu", renamed=False
            )
        new_full_path = full_path.parent / new_name
        if new_full_path.exists() and new_full_path != full_path:
            stem = Path(new_name).stem
            suffix = Path(new_name).suffix
            counter = 1
            while new_full_path.exists():
                new_name = f"{stem}_{counter}{suffix}"
                new_full_path = full_path.parent / new_name
                counter += 1
                if counter > 100:
                    return RenameResult(
                        old_path=file_path, new_path="",
                        old_name=old_name, new_name=new_name,
                        reason="", renamed=False,
                        error="Khong the tao ten khong trung sau 100 lan thu"
                    )
        reason_text = "; ".join(reasons)
        if dry_run:
            new_rel = str(new_full_path.relative_to(ws))
            return RenameResult(
                old_path=file_path, new_path=new_rel,
                old_name=old_name, new_name=new_name,
                reason=reason_text, renamed=False
            )
        try:
            full_path.rename(new_full_path)
            new_rel = str(new_full_path.relative_to(ws))
            return RenameResult(
                old_path=file_path, new_path=new_rel,
                old_name=old_name, new_name=new_name,
                reason=reason_text, renamed=True
            )
        except Exception as e:
            return RenameResult(
                old_path=file_path, new_path="",
                old_name=old_name, new_name=new_name,
                reason=reason_text, renamed=False, error=str(e)
            )

    def auto_rename_all(self, workspace_path: str,
                        recursive: bool = True,
                        dry_run: bool = True,
                        skip_dirs: Optional[List[str]] = None) -> BatchRenameResult:
        result = BatchRenameResult()
        problematic = self.scan_workspace(workspace_path, recursive, skip_dirs)
        result.total_scanned = len(problematic)

        if not problematic:
            ws = Path(workspace_path)
            _skip = skip_dirs or []
            total_files = sum(1 for _ in ws.rglob("*") if _.is_file()
                              and not _.name.startswith('.')
                              and not any(p in _skip for p in _.relative_to(ws).parts))
            result.total_scanned = total_files
            result.total_problematic = 0
            return result

        result.total_problematic = len(problematic)

        try:
            ws = Path(workspace_path)
            _skip = skip_dirs or []
            total_scanned = 0
            for item in ws.rglob("*"):
                if item.is_file() and not item.name.startswith('.'):
                    parts = item.relative_to(ws).parts
                    if not any(p in _skip for p in parts):
                        total_scanned += 1
            result.total_scanned = total_scanned
        except Exception:
            result.total_scanned = len(problematic)

        for file_path in problematic:
            rename_result = self.rename_file(file_path, workspace_path, dry_run)
            result.results.append(rename_result)
            if rename_result.error:
                result.total_errors += 1
            elif rename_result.renamed:
                result.total_renamed += 1
            else:
                result.total_skipped += 1

        return result

    def format_results(self, batch_result: BatchRenameResult,
                       dry_run: bool = True) -> str:
        if dry_run:
            header = "*** KET QUA QUET VA DE XUAT DOI TEN FILE (DRY-RUN) ***"
            action_note = (
                "\n[!] Day la che do XEM TRUOC (dry-run). "
                "Chua co file nao bi doi ten that.\n"
                "De thuc thi, dung --execute."
            )
        else:
            header = "*** KET QUA DOI TEN FILE ***"
            action_note = ""

        lines = [
            header,
            "=" * 60,
            "",
            f"Thong ke:",
            f"   - Tong so file da quet: {batch_result.total_scanned}",
            f"   - File co van de: {batch_result.total_problematic}",
            f"   - Da doi ten: {batch_result.total_renamed}",
            f"   - Bo qua: {batch_result.total_skipped}",
            f"   - Loi: {batch_result.total_errors}",
            action_note,
            "",
        ]

        if batch_result.results:
            lines.append(f"Chi tiet ({len(batch_result.results)} file):")
            lines.append("")
            for i, r in enumerate(batch_result.results, 1):
                status = "[RENAMED]" if r.renamed else ("[ERROR]" if r.error else "[PROPOSED]")
                lines.append(f"  {i}. {status} {r.old_path}")
                lines.append(f"     Ly do: {r.reason}")
                if r.error:
                    lines.append(f"     Loi: {r.error}")
                elif r.old_name != r.new_name:
                    lines.append(f"     De xuat: {r.new_name}")
                    if r.renamed:
                        lines.append(f"     Da doi thanh: {r.new_path}")
                lines.append("")
        else:
            lines.append("Khong tim thay file nao can doi ten.")
            lines.append("Tat ca ten file trong workspace deu dat chuan.")

        lines.append("-" * 60)
        lines.append("Tieu chi phat hien file can doi ten:")
        lines.append("   - Ten co chua tieng Viet co dau")
        lines.append(f"   - Ten dai hon {self.max_name_length} ky tu")
        lines.append("   - Ten chua ky tu dac biet")
        lines.append("   - Ten co nhieu khoang trang/gach duoi lien tiep")
        lines.append("")
        lines.append("Cach xu ly:")
        lines.append("   - Chuan hoa Unicode (NFC)")
        lines.append("   - Chuyen co dau -> khong dau")
        lines.append("   - Viet tat cac tu/cum tu pho bien")
        lines.append("   - Rut gon ten dai, giu tu khoa chinh")
        lines.append("   - Loai bo ky tu dac biet")

        return "\n".join(lines)


# ============================================================
# CLI Interface
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="File Renamer - Tu dong chuan hoa ten file tieng Viet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python file_renamer.py --path D:\\workspace --dry-run
  python file_renamer.py --path D:\\workspace --execute
  python file_renamer.py --path D:\\workspace --subdir "Kho_tai_lieu" --dry-run
  python file_renamer.py --path D:\\workspace --file "Quyet dinh khoi to.docx" --dry-run
        """
    )
    parser.add_argument('--path', '-p', required=True,
                        help='Duong dan den thu muc workspace can quet')
    parser.add_argument('--dry-run', '-n', action='store_true', default=True,
                        help='Chi xem truoc, khong doi ten that (mac dinh)')
    parser.add_argument('--execute', '-x', action='store_true',
                        help='Thuc thi doi ten that (can than!)')
    parser.add_argument('--subdir', '-s', default='',
                        help='Thu muc con can quet (de trong = quet tat ca)')
    parser.add_argument('--file', '-f', default='',
                        help='Chi doi ten 1 file cu the')
    parser.add_argument('--max-length', '-m', type=int, default=60,
                        help='Do dai toi da cho ten file (mac dinh: 60)')

    args = parser.parse_args()

    # Force UTF-8 output
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    dry_run = not args.execute
    renamer = FileRenamer(max_name_length=args.max_length)

    if args.file:
        # Single file rename
        result = renamer.rename_file(args.file, args.path, dry_run=dry_run)
        if result.error:
            print(f"LOI: {result.error}")
            return 1
        if not dry_run and result.renamed:
            print(f"DA DOI TEN: {result.old_path} -> {result.new_name}")
            print(f"  Ly do: {result.reason}")
        elif result.old_name == result.new_name:
            print(f"KHONG CAN DOI: {result.old_name} - {result.reason}")
        else:
            print(f"DE XUAT: {result.old_name} -> {result.new_name}")
            print(f"  Ly do: {result.reason}")
            print("  (Dung --execute de thuc thi)")
    else:
        # Batch rename
        target = args.path
        if args.subdir:
            target = str(Path(args.path) / args.subdir)
            if not Path(target).is_dir():
                print(f"LOI: Thu muc khong ton tai: {target}")
                return 1

        result = renamer.auto_rename_all(target, recursive=True, dry_run=dry_run)
        formatted = renamer.format_results(result, dry_run=dry_run)
        print(formatted)

    return 0


if __name__ == "__main__":
    sys.exit(main())