"""
RTF (Rich Text Format) formatter.

Produces .rtf files with formatted exam content.
"""

from pathlib import Path
from typing import Union

from .formatter import BaseFormatter, ExamType, BODY_SIZE
from .parser import ParsedExam, Question, Answer


class RTFFormatter(BaseFormatter):
    """
    Formatter that produces RTF (.rtf) files.

    Applies formatting rules similar to Word output:
    - Times New Roman, 12pt font
    - 2-line centered bold header (Title + section name)
    - Questions numbered with text
    - Choices indented
    - Page break before answer key
    """

    # RTF uses twips (1/20 of a point) for measurements
    TWIPS_PER_POINT = 20
    TWIPS_PER_INCH = 1440

    def __init__(self):
        super().__init__()
        self.font_size_twips = BODY_SIZE * 2  # RTF font size is in half-points
        self.margin_twips = int(self.margin * self.TWIPS_PER_INCH)
        self.indent_twips = int(self.choice_indent * self.TWIPS_PER_INCH)

    def get_extension(self) -> str:
        return '.rtf'

    def format(self, exam: ParsedExam, output_path: Union[str, Path],
               exam_type: ExamType = ExamType.FINAL) -> Path:
        output_path = self.ensure_extension(output_path)

        title = exam.title or "Exam"

        # Build RTF document
        rtf_content = self._build_rtf_document(exam, title, exam_type)

        output_path.write_text(rtf_content, encoding='utf-8')

        return output_path

    def _build_rtf_document(self, exam: ParsedExam, title: str,
                            exam_type: ExamType) -> str:
        """Build complete RTF document."""
        parts = []

        # RTF header with font table
        parts.append(self._get_rtf_header())

        # Document formatting (margins)
        parts.append(self._get_document_formatting())

        # Questions section header
        parts.append(self._format_header(title, "Questions"))
        parts.append(r'\par')

        # Questions
        for question in exam.questions:
            parts.append(self._format_question(question))

        # Answer key section (with page break)
        if exam.answers:
            parts.append(r'\page')  # Page break
            parts.append(self._format_header(title, "Answer Key"))
            parts.append(r'\par')

            for answer in exam.answers:
                parts.append(self._format_answer(answer, exam_type))

        # Close document
        parts.append('}')

        return '\n'.join(parts)

    def _get_rtf_header(self) -> str:
        """Generate RTF header with font table."""
        return (
            r'{\rtf1\ansi\deff0'
            r'{\fonttbl{\f0\froman Times New Roman;}}'
            r'{\colortbl;\red0\green0\blue0;}'
        )

    def _get_document_formatting(self) -> str:
        """Generate document-level formatting."""
        return (
            f'\\margl{self.margin_twips}'
            f'\\margr{self.margin_twips}'
            f'\\margt{self.margin_twips}'
            f'\\margb{self.margin_twips}'
            f'\\fs{self.font_size_twips}'
        )

    def _format_header(self, title: str, section_name: str) -> str:
        """Format centered bold header."""
        # Header is 20pt bold centered
        header_size = 20 * 2  # half-points
        title_escaped = self._escape_rtf(title)
        section_escaped = self._escape_rtf(section_name)
        return (
            f'\\pard\\qc\\b\\fs{header_size} {title_escaped}\\par\n'
            f'{section_escaped}\\b0\\fs{self.font_size_twips}\\par\n'
            f'\\pard\\ql'
        )

    def _format_question(self, question: Question) -> str:
        """Format a question and its choices."""
        parts = []

        # Question text
        q_text = self._escape_rtf(question.text)
        parts.append(f'\\par {question.number}.\\tab {q_text}\\par')

        # Choices with indentation
        for choice in question.choices:
            c_text = self._escape_rtf(choice.text)
            parts.append(
                f'\\li{self.indent_twips} {choice.letter}.\\tab {c_text}\\par'
            )

        # Reset indentation and add blank line
        parts.append('\\li0\\par')

        return '\n'.join(parts)

    def _format_answer(self, answer: Answer, exam_type: ExamType) -> str:
        """Format an answer key entry."""
        payload = self._escape_rtf(answer.payload)

        if exam_type == ExamType.PRACTICE:
            return f'\\par {answer.question_number}.\\tab {answer.answer_letter}\\tab {payload}\\par'
        else:
            return f'\\par {answer.question_number}.\\tab {answer.answer_letter})\\tab {payload}\\par'

    def _escape_rtf(self, text: str) -> str:
        """Escape special RTF characters."""
        if not text:
            return ''

        # RTF special characters
        text = text.replace('\\', '\\\\')
        text = text.replace('{', '\\{')
        text = text.replace('}', '\\}')

        # Handle non-ASCII characters
        result = []
        for char in text:
            if ord(char) > 127:
                result.append(f"\\u{ord(char)}?")
            else:
                result.append(char)

        return ''.join(result)
