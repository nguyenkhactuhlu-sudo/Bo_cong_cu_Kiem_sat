import re
from pathlib import Path

from docx import Document


class DocxIO:
    def __init__(self, filepath):
        self.doc = Document(str(Path(filepath)))
        self.filepath = str(Path(filepath))

    def _iter_paragraphs(self):
        """Duyệt đoạn văn trong thân bài, bảng, đầu trang và chân trang."""
        seen = set()

        def emit(paragraphs):
            for paragraph in paragraphs:
                # Giữ trực tiếp phần tử XML trong set; dùng id() có thể trùng lại
                # khi wrapper Paragraph tạm thời bị thu hồi trong lúc duyệt.
                marker = paragraph._p
                if marker not in seen:
                    seen.add(marker)
                    yield paragraph

        yield from emit(self.doc.paragraphs)
        for table in self.doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    yield from emit(cell.paragraphs)
                    for nested in cell.tables:
                        for nested_row in nested.rows:
                            for nested_cell in nested_row.cells:
                                yield from emit(nested_cell.paragraphs)

        for section in self.doc.sections:
            yield from emit(section.header.paragraphs)
            yield from emit(section.footer.paragraphs)

    def get_text(self):
        return '\n'.join(paragraph.text for paragraph in self._iter_paragraphs())

    @staticmethod
    def _find_matches(text, old):
        if not old:
            return []
        # Không thay "An" bên trong "An Giang"/một từ dài hơn theo kiểu chuỗi con.
        left = r'(?<!\w)' if old[0].isalnum() or old[0] == '_' else ''
        right = r'(?!\w)' if old[-1].isalnum() or old[-1] == '_' else ''
        return list(re.finditer(left + re.escape(old) + right, text))

    def _replace_in_paragraph(self, paragraph, old, new):
        runs = paragraph.runs
        if not runs:
            return 0

        full_text = ''.join(run.text for run in runs)
        matches = self._find_matches(full_text, old)
        if not matches:
            return 0

        offsets = []
        position = 0
        for index, run in enumerate(runs):
            offsets.append((position, position + len(run.text), index))
            position += len(run.text)

        def locate(char_index):
            for start, end, run_index in offsets:
                if start <= char_index < end:
                    return run_index, char_index - start
            return len(runs) - 1, len(runs[-1].text)

        # Thay từ cuối về đầu để vị trí phía trước không bị dịch chuyển.
        for match in reversed(matches):
            start_run, start_offset = locate(match.start())
            end_run, end_offset = locate(match.end() - 1)
            end_offset += 1
            if start_run == end_run:
                text = runs[start_run].text
                runs[start_run].text = text[:start_offset] + new + text[end_offset:]
                continue

            prefix = runs[start_run].text[:start_offset]
            suffix = runs[end_run].text[end_offset:]
            runs[start_run].text = prefix + new
            for run_index in range(start_run + 1, end_run):
                runs[run_index].text = ''
            runs[end_run].text = suffix
        return len(matches)

    def replace_text(self, old, new):
        count = 0
        for paragraph in self._iter_paragraphs():
            count += self._replace_in_paragraph(paragraph, old, new)
        return count

    def save(self, path):
        self.doc.save(path)
