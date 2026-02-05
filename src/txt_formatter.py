"""
Plain text formatter.

Produces .txt files with clean formatting for exam content.
"""

from pathlib import Path
from typing import Union

from .formatter import BaseFormatter, ExamType
from .parser import ParsedExam, Question, Answer


class TxtFormatter(BaseFormatter):
    """
    Formatter that produces plain text (.txt) files.

    Applies formatting rules:
    - 2-line centered header (Title + section name)
    - Questions formatted as "#.\\t<text>"
    - Choices indented with spaces as "    A.\\t<text>"
    - Blank line after each choice
    - Page break indicator before answer key
    - Practice answers: "#.\\t<letter>\\t<code ref>"
    - Final answers: "#.\\t<letter>)\\t<source> (<citation>)"
    """

    CHOICE_INDENT = "    "  # 4 spaces
    HEADER_WIDTH = 60  # Width for centering header text

    def get_extension(self) -> str:
        return '.txt'

    def format(self, exam: ParsedExam, output_path: Union[str, Path],
               exam_type: ExamType = ExamType.FINAL) -> Path:
        output_path = self.ensure_extension(output_path)

        lines = []
        title = exam.title or "Exam"

        # Questions header
        lines.extend(self._format_header(title, "Questions"))
        lines.append("")

        # Add questions
        for question in exam.questions:
            lines.extend(self._format_question(question))

        # Add answer key section
        if exam.answers:
            lines.append("")
            lines.append("=" * self.HEADER_WIDTH)
            lines.append("")
            lines.extend(self._format_header(title, "Answer Key"))
            lines.append("")

            for answer in exam.answers:
                lines.append(self._format_answer(answer, exam_type))
                lines.append("")

        content = "\n".join(lines)
        output_path.write_text(content, encoding='utf-8')

        return output_path

    def _format_header(self, title: str, section_name: str) -> list[str]:
        """Create centered 2-line header."""
        return [
            title.center(self.HEADER_WIDTH),
            section_name.center(self.HEADER_WIDTH),
        ]

    def _format_question(self, question: Question) -> list[str]:
        """Format a question and its choices as text lines."""
        lines = []

        lines.append(f"{question.number}.\t{question.text}")
        lines.append("")

        for choice in question.choices:
            lines.append(f"{self.CHOICE_INDENT}{choice.letter}.\t{choice.text}")
            lines.append("")

        return lines

    def _format_answer(self, answer: Answer, exam_type: ExamType) -> str:
        """Format an answer key entry as a single line."""
        if exam_type == ExamType.PRACTICE:
            return f"{answer.question_number}.\t{answer.answer_letter}\t{answer.payload}"
        else:
            return f"{answer.question_number}.\t{answer.answer_letter})\t{answer.payload}"
