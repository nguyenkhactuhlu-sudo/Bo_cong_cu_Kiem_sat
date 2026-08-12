import re


class PIIDetector:
    """Bộ nhận diện PII dựa trên quy tắc cho văn bản tố tụng tiếng Việt."""

    WORD = r"[^\W\d_]+(?:[-'][^\W\d_]+)?"
    NAME_WORDS = rf"{WORD}(?:\s+{WORD}){{0,4}}"

    HONORIFICS = (
        'ông', 'bà', 'anh', 'chị', 'cô', 'chú', 'bác', 'dì', 'cậu',
        'thím', 'em', 'cháu', 'ngài', 'bị cáo', 'bị can', 'nguyên đơn',
        'bị đơn', 'người bị hại', 'người có quyền lợi, nghĩa vụ liên quan',
        'người làm chứng', 'đương sự', 'vợ', 'chồng', 'con trai', 'con gái'
    )

    COMMON_SURNAMES = (
        'Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ',
        'Võ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương', 'Lý', 'Đinh',
        'Đoàn', 'Trịnh', 'Mai', 'Cao', 'Tô', 'Tạ', 'Lâm', 'Quách'
    )

    NON_NAME_TERMS = (
        'bộ luật', 'cộng hòa', 'xã hội chủ nghĩa', 'việt nam', 'tòa án',
        'viện kiểm sát', 'ủy ban', 'hội đồng', 'công an', 'quyết định',
        'bản án', 'thông báo', 'biên bản', 'nghị quyết', 'điều luật',
        'blhs', 'blds', 'tand', 'vksnd', 'ubnd', 'hđnd'
    )

    def __init__(self, text):
        self.text = text or ''

    def detect(self):
        entities = []
        entities.extend(self._detect_phone())
        entities.extend(self._detect_cccd())
        entities.extend(self._detect_cmnd())
        entities.extend(self._detect_address())
        entities.extend(self._detect_names())
        return self._deduplicate(entities)

    def _detect_phone(self):
        phones = set()
        # Chấp nhận số liền hoặc có dấu cách/chấm/gạch ngang.
        pattern = r'(?<!\d)(?:\+84|0)(?:[ .-]?\d){9,10}(?!\d)'
        for match in re.finditer(pattern, self.text):
            value = match.group().strip()
            digits = re.sub(r'\D', '', value)
            if value.startswith('+84'):
                valid = len(digits) in (11, 12)
            else:
                valid = len(digits) in (10, 11)
            if valid:
                phones.add(value)
        return [
            {'type': 'SĐT', 'value': value, 'suggestion': self._mask_phone(value)}
            for value in sorted(phones, key=self.text.find)
        ]

    def _detect_cccd(self):
        items = {m.group() for m in re.finditer(r'(?<!\d)\d{12}(?!\d)', self.text)}
        return [
            {'type': 'CCCD', 'value': value, 'suggestion': self._mask_number(value)}
            for value in sorted(items, key=self.text.find)
        ]

    def _detect_cmnd(self):
        items = {m.group() for m in re.finditer(r'(?<!\d)\d{9}(?!\d)', self.text)}
        return [
            {'type': 'CMND', 'value': value, 'suggestion': self._mask_number(value)}
            for value in sorted(items, key=self.text.find)
        ]

    def _detect_address(self):
        addresses = set()
        label = (
            r'trú tại|địa chỉ|thường trú|HKTT|nơi ở|chỗ ở|nhà số|'
            r'nơi cư trú|hộ khẩu thường trú'
        )
        # Giữ dấu phẩy trong địa chỉ; dừng ở cuối câu/dòng hoặc trường kế tiếp.
        stop = (
            r'(?=\s*(?:[.;\n]|số điện thoại\s*:|điện thoại\s*:|'
            r'CCCD\s*:|CMND\s*:|sinh năm\s*:|$))'
        )
        pattern = rf'(?:{label})\s*[:\-]?\s*(.+?){stop}'
        for match in re.finditer(pattern, self.text, re.IGNORECASE):
            address = match.group(1).strip(' ,:-')
            if len(address) >= 5:
                addresses.add(address)
        return [
            {'type': 'Địa chỉ', 'value': value, 'suggestion': self._mask_address(value)}
            for value in sorted(addresses, key=self.text.find)
        ]

    def _detect_names(self):
        found_names = set()
        address_ranges = []
        for entity in self._detect_address():
            start = 0
            while True:
                start = self.text.find(entity['value'], start)
                if start < 0:
                    break
                address_ranges.append((start, start + len(entity['value'])))
                start += len(entity['value'])

        def add_candidate(raw_value, start):
            candidate = self._clean_name(raw_value)
            end = start + len(candidate)
            if any(start < address_end and end > address_start for address_start, address_end in address_ranges):
                return
            if self._is_probable_name(candidate):
                found_names.add(candidate)

        honorific_pattern = '|'.join(
            re.escape(item) for item in sorted(self.HONORIFICS, key=len, reverse=True)
        )
        labelled_patterns = [
            rf'(?<!\w)(?:{honorific_pattern})\s*[:\-]?\s+({self.NAME_WORDS})',
            rf'(?<!\w)(?:họ\s*(?:và)?\s*tên|họ tên|tên người)\s*[:\-]\s*({self.NAME_WORDS})',
        ]
        for pattern in labelled_patterns:
            for match in re.finditer(pattern, self.text, re.IGNORECASE):
                add_candidate(match.group(1), match.start(1))

        # Tên không có danh xưng chỉ được nhận khi bắt đầu bằng một họ phổ biến.
        surname_pattern = '|'.join(re.escape(item) for item in self.COMMON_SURNAMES)
        pattern = rf'(?<!\w)((?:{surname_pattern})(?:\s+{self.WORD}){{1,4}})'
        for match in re.finditer(pattern, self.text, re.IGNORECASE):
            add_candidate(match.group(1), match.start(1))

        # Giữ cụm dài hơn nếu một kết quả chỉ là phần nguyên vẹn của cụm dài đó.
        names = sorted(found_names, key=lambda value: (-len(value.split()), self.text.casefold().find(value.casefold())))
        kept = []
        for name in names:
            normalized = self._normalize(name)
            if any(
                normalized != self._normalize(existing)
                and re.search(rf'(?<!\w){re.escape(normalized)}(?!\w)', self._normalize(existing))
                for existing in kept
            ):
                continue
            kept.append(name)

        kept.sort(key=lambda value: self.text.casefold().find(value.casefold()))
        return [
            {'type': 'Tên', 'value': name, 'suggestion': self._generate_alias(index)}
            for index, name in enumerate(kept)
        ]

    def _clean_name(self, value):
        # Các từ sau thường bắt đầu một trường/cụm mới, không thuộc tên người.
        value = re.split(
            r'\s+(?=sinh\s+năm|sinh\s+ngày|địa\s+chỉ|trú\s+tại|'
            r'thường\s+trú|CCCD|CMND|là\s+|có\s+|đã\s+)',
            value.strip(), maxsplit=1, flags=re.IGNORECASE
        )[0]
        value = value.strip(' ,.;:()[]{}-')
        # Regex lấy dư tối đa 5 từ; cắt ngay khi gặp từ thường như "và", "có", "vắng".
        name_words = []
        for word in value.split():
            cleaned_word = word.strip(' ,.;:()[]{}-')
            if not cleaned_word or not re.fullmatch(self.WORD, cleaned_word):
                break
            if not cleaned_word[0].isupper():
                break
            name_words.append(cleaned_word)
        return ' '.join(name_words)

    def _is_probable_name(self, candidate):
        words = candidate.split()
        if not 2 <= len(words) <= 5:
            return False
        normalized = self._normalize(candidate)
        if any(term in normalized for term in self.NON_NAME_TERMS):
            return False
        if any(not re.fullmatch(self.WORD, word) for word in words):
            return False
        # Tránh bắt cả câu chữ thường; mỗi thành tố tên phải viết hoa hoặc viết in hoa.
        return all(word[0].isupper() for word in words)

    @staticmethod
    def _normalize(value):
        return re.sub(r'\s+', ' ', value).strip().casefold()

    def _mask_phone(self, phone):
        digits = re.sub(r'\D', '', phone)
        if len(digits) >= 7:
            return digits[:4] + 'xxxx' + digits[-3:]
        return '[SĐT]'

    def _mask_number(self, number):
        if len(number) >= 6:
            return number[:3] + 'xxx' + number[-3:]
        return '[Số]'

    @staticmethod
    def _mask_address(_address):
        return 'Địa chỉ [Đã ẩn]'

    @staticmethod
    def _generate_alias(index):
        if index < 26:
            return f'Tên-{chr(65 + index)}'
        return f'Tên-{index + 1}'

    def _deduplicate(self, entities):
        seen = set()
        result = []
        for entity in entities:
            key = (entity['type'], self._normalize(entity['value']))
            if key not in seen:
                seen.add(key)
                result.append(entity)
        return result
