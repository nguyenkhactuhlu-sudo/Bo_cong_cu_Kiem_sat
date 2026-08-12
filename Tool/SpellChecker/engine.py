"""Bộ rà lỗi tiếng Việt dựa trên từ điển và luật xác định, không dùng AI."""

from __future__ import annotations

import difflib
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path


LETTER_MARK = r"(?:[^\W\d_]|[\u0300-\u036f])"
WORD_RE = re.compile(LETTER_MARK + r"+(?:[-']" + LETTER_MARK + r"+)*", re.UNICODE)


@dataclass
class Issue:
    id: str
    kind: str
    severity: str
    start: int
    end: int
    original: str
    suggestion: str
    message: str
    confidence: int
    paragraph_id: str = ""
    location: str = ""
    context: str = ""

    def to_dict(self):
        return asdict(self)


# Luật chắc chắn cao. Cụm dài phải đứng trước cụm ngắn.
COMMON_ERRORS = {
    "viện kiểm xát": "viện kiểm sát",
    "kiểm xát viên": "kiểm sát viên",
    "thực hành quyển công tố": "thực hành quyền công tố",
    "quyết định khỏi tố": "quyết định khởi tố",
    "quyêt định": "quyết định",
    "khởi tộ": "khởi tố",
    "truy té": "truy tố",
    "bị cao": "bị cáo",
    "cáo chạng": "cáo trạng",
    "tạm dữ": "tạm giữ",
    "tạm giử": "tạm giữ",
    "tạm ghim": "tạm giam",
    "thẩm quyển": "thẩm quyền",
    "điểu tra": "điều tra",
    "kiễm sát": "kiểm sát",
    "kiểm xát": "kiểm sát",
    "trách nhiêm": "trách nhiệm",
    "pháp luât": "pháp luật",
    "bổ xung": "bổ sung",
    "xát nhập": "sáp nhập",
    "sát nhập": "sáp nhập",
    "chuẩn đoán": "chẩn đoán",
    "tham ô tài sãn": "tham ô tài sản",
    "xâm phạm sở hửu": "xâm phạm sở hữu",
    "vật chứn": "vật chứng",
    "bút lụt": "bút lục",
    "biên bãn": "biên bản",
    "đương sư": "đương sự",
    "thi hành áng": "thi hành án",
}

LEGAL_WORDS = """
án phí bút lục bị can bị cáo bị hại đương sự nguyên đơn bị đơn công tố kiểm sát
kiểm sát viên kiểm sát việc khởi tố truy tố điều tra xét xử thi hành án tạm giữ
tạm giam cáo trạng luận tội kháng nghị kháng cáo kiến nghị đình chỉ giám định
định giá vật chứng chứng cứ tố giác tin báo phạm tội thi hành quyền công tố
trách nhiệm hình sự dân sự hành chính phúc thẩm sơ thẩm giám đốc thẩm tái thẩm
ủy thác tư pháp tương trợ tư pháp cơ quan điều tra hội đồng xét xử quyết định
biên bản lệnh thông báo kết luận bản án thời hạn thời hiệu thẩm quyền
""".split()

ACRONYMS = {
    "VKS", "VKSND", "VKSNDTC", "CQĐT", "CAND", "TAND", "TANDTC", "BLHS",
    "BLTTHS", "BLDS", "BLTTDS", "CCCD", "CMND", "UBND", "HĐND", "QĐ",
    "TTLT", "NĐ", "CP", "QH", "PDF", "DOCX", "TP", "KSND",
}

# Ký hiệu đơn vị thường xuất hiện trong biên bản, kết luận giám định và hồ sơ
# nghiệp vụ. Tất cả được so sánh sau khi casefold nên chỉ cần lưu dạng chữ
# thường. Chỉ miễn kiểm tra khi ký hiệu thực sự đi sau một giá trị số.
MEASUREMENT_UNITS = {
    # Độ dài, diện tích, thể tích
    "mm", "cm", "dm", "dam", "hm", "km", "in", "ft", "yd",
    "mm2", "cm2", "dm2", "m2", "km2", "mm3", "cm3", "dm3", "m3",
    # Khối lượng, dung tích
    "mcg", "μg", "µg", "mg", "kg", "ml", "cl", "dl",
    # Điện, công suất, tần số, áp suất và dữ liệu
    "ma", "ka", "mv", "kv", "mw", "kw", "hz", "khz", "mhz", "ghz",
    "pa", "kpa", "mpa", "bar", "kb", "mb", "gb", "tb",
}

# Từ điển CSpell đang dùng có nhiều mục đặt dấu theo kiểu cũ (hoà, toà,
# thoả, tuỳ...). Ứng dụng cần chấp nhận thêm kiểu đặt dấu hiện hành
# (hòa, tòa, thỏa, tùy...). Trường hợp "qu" được loại trừ vì các từ như
# "quý", "quỳ" vốn đã đặt dấu đúng trên y.
MODERN_TONE_REPLACEMENTS = (
    ("oà", "òa"), ("oá", "óa"), ("oả", "ỏa"), ("oã", "õa"), ("oạ", "ọa"),
    ("oè", "òe"), ("oé", "óe"), ("oẻ", "ỏe"), ("oẽ", "õe"), ("oẹ", "ọe"),
)


def modernize_tone_placement(word: str) -> str:
    """Chuyển một mục từ kiểu đặt dấu cũ sang biến thể hiện hành."""
    converted = word
    for old, modern in MODERN_TONE_REPLACEMENTS:
        converted = converted.replace(old, modern)
    converted = re.sub("(?<!q)uỳ", "ùy", converted)
    converted = re.sub("(?<!q)uý", "úy", converted)
    converted = re.sub("(?<!q)uỷ", "ủy", converted)
    converted = re.sub("(?<!q)uỹ", "ũy", converted)
    converted = re.sub("(?<!q)uỵ", "ụy", converted)
    return converted


def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    direct = base / relative
    if direct.exists():
        return direct
    return Path(__file__).resolve().parent / relative


def strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(ch for ch in unicodedata.normalize("NFD", text)
                   if unicodedata.category(ch) != "Mn")


class VietnameseSpellChecker:
    def __init__(self, dictionary_path: str | Path | None = None):
        path = Path(dictionary_path) if dictionary_path else resource_path("data/vi.dic")
        lines = path.read_text(encoding="utf-8").splitlines()
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        dictionary_words = {
            unicodedata.normalize("NFC", line.split("/", 1)[0]).casefold()
            for line in lines if line.strip()
        }
        self.words = set(dictionary_words)
        self.words.update(modernize_tone_placement(word) for word in dictionary_words)
        self.words.update(w.casefold() for w in LEGAL_WORDS)
        self.by_length: dict[int, list[str]] = {}
        for word in self.words:
            self.by_length.setdefault(len(word), []).append(word)
        self.errors = sorted(COMMON_ERRORS.items(), key=lambda pair: len(pair[0]), reverse=True)

    def _context(self, text: str, start: int, end: int, radius: int = 55) -> str:
        left = max(0, start - radius)
        right = min(len(text), end + radius)
        return ("…" if left else "") + text[left:right].replace("\n", " ") + ("…" if right < len(text) else "")

    @staticmethod
    def _protected_ranges(text: str):
        patterns = [
            r"https?://\S+", r"\b[\w.+-]+@[\w.-]+\.\w+\b",
            r"\b\d+[A-ZĐ]?[-/.]\d[\w./-]*\b", r"\b[A-ZĐ]{2,12}\b",
        ]
        ranges = []
        for pattern in patterns:
            ranges.extend((m.start(), m.end()) for m in re.finditer(pattern, text, re.UNICODE))
        # Tên riêng sau các nhãn nghiệp vụ được bảo vệ khỏi báo lỗi từ điển.
        label = r"(?:ông|bà|anh|chị|bị can|bị cáo|bị hại|đương sự|nguyên đơn|bị đơn)\s+"
        name = r"(?:[A-ZĐ][^\W\d_]+(?:\s+|$)){2,5}"
        ranges.extend((m.start(), m.end()) for m in re.finditer(label + name, text))
        return ranges

    @staticmethod
    def _is_protected(start: int, end: int, ranges) -> bool:
        return any(start < b and end > a for a, b in ranges)

    @staticmethod
    def _is_measurement_unit(text: str, start: int, token: str) -> bool:
        """Chỉ nhận ký hiệu đơn vị khi phía trước là số hoặc khoảng số."""
        if token.casefold() not in MEASUREMENT_UNITS:
            return False
        prefix = text[max(0, start - 40):start]
        number = r"\d+(?:[.,]\d+)?"
        interval = rf"{number}(?:\s*(?:-|–|—|đến)\s*{number})?"
        return re.search(rf"{interval}\s*$", prefix, re.IGNORECASE) is not None

    @lru_cache(maxsize=4096)
    def suggest(self, word: str, limit: int = 3) -> tuple[str, ...]:
        source = unicodedata.normalize("NFC", word).casefold()
        skeleton = strip_accents(source)
        candidates = []
        for length in range(max(1, len(source) - 2), len(source) + 3):
            for candidate in self.by_length.get(length, ()):
                base_ratio = difflib.SequenceMatcher(None, skeleton, strip_accents(candidate)).ratio()
                if base_ratio >= 0.67:
                    exact_ratio = difflib.SequenceMatcher(None, source, candidate).ratio()
                    score = exact_ratio * 0.65 + base_ratio * 0.35
                    candidates.append((score, candidate))
        candidates.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
        return tuple(candidate for _, candidate in candidates[:limit])

    def check_text(self, text: str, paragraph_id: str = "", location: str = "") -> list[Issue]:
        issues: list[Issue] = []
        occupied: list[tuple[int, int]] = []

        def add(kind, severity, start, end, suggestion, message, confidence):
            if any(start < b and end > a for a, b in occupied):
                return
            original = text[start:end]
            issues.append(Issue(
                id="", kind=kind, severity=severity, start=start, end=end,
                original=original, suggestion=suggestion, message=message,
                confidence=confidence, paragraph_id=paragraph_id, location=location,
                context=self._context(text, start, end),
            ))
            occupied.append((start, end))

        # 1. Cụm sai đã xác nhận.
        for wrong, right in self.errors:
            for match in re.finditer(r"(?<!\w)" + re.escape(wrong) + r"(?!\w)", text, re.IGNORECASE):
                replacement = right
                if match.group(0)[:1].isupper():
                    replacement = replacement[:1].upper() + replacement[1:]
                add("Cụm từ", "error", match.start(), match.end(), replacement,
                    "Cụm từ sai hoặc không phù hợp trong văn bản nghiệp vụ.", 99)

        # 2. Khoảng trắng và dấu câu – chỉ báo những mẫu ít gây nhầm.
        formatting_rules = [
            (r"[ \t]{2,}", " ", "Có nhiều khoảng trắng liên tiếp."),
            (r"\s+([,;:!?])", r"\1", "Có khoảng trắng thừa trước dấu câu."),
            (r"([,;:!?])(?=[^\s\d\n])", r"\1 ", "Thiếu khoảng trắng sau dấu câu."),
            (r"([!?;,])\1+", r"\1", "Dấu câu bị lặp."),
        ]
        for pattern, replacement, message in formatting_rules:
            for match in re.finditer(pattern, text):
                suggestion = match.expand(replacement)
                add("Trình bày", "style", match.start(), match.end(), suggestion, message, 98)

        # 3. Từ/âm tiết không có trong từ điển. Unicode tổ hợp được chuẩn hóa
        # nội bộ chỉ để tra cứu, không bị coi là lỗi và không làm đổi văn bản gốc.
        protected = self._protected_ranges(text)
        for match in WORD_RE.finditer(text):
            start, end = match.span()
            if any(start < b and end > a for a, b in occupied) or self._is_protected(start, end, protected):
                continue
            token = unicodedata.normalize("NFC", match.group(0))
            folded = token.casefold()
            if (len(folded) <= 1 or folded in self.words or token in ACRONYMS
                    or self._is_measurement_unit(text, start, token)):
                continue
            if token.isupper() or any(ch.isdigit() for ch in token):
                continue
            # Tên riêng viết hoa giữa câu: chỉ cảnh báo khi có gợi ý rất gần.
            suggestions = self.suggest(folded)
            if not suggestions:
                continue
            ratio = difflib.SequenceMatcher(None, folded, suggestions[0]).ratio()
            threshold = 0.86 if token[:1].isupper() else 0.78
            if ratio < threshold:
                continue
            suggestion = suggestions[0]
            if token[:1].isupper():
                suggestion = suggestion[:1].upper() + suggestion[1:]
            confidence = min(95, max(62, round(ratio * 100)))
            add("Chính tả", "warning", start, end, suggestion,
                "Từ không có trong từ điển tiếng Việt; cần kiểm tra lại.", confidence)

        issues.sort(key=lambda item: (item.start, -(item.end - item.start), item.kind))
        for index, issue in enumerate(issues, 1):
            issue.id = f"{paragraph_id}:{index}"
        return issues
