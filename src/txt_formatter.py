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
    - Questions formatted as "#.\\t<text>"
    - Choices indented with spaces as "    A.\\t<text>"
    - Blank line after each choice
    - Page break indicator before answer key
    - Practice answers: "#.\\t<letter>\\t<code ref>"
    - Final answers: "#.\\t<letter>)\\t<source> (<citation>)"
    """

    # Number of spaces for choice indentation (simulating 0.25 inch)
    CHOICE_INDENT = "    "  # 4 spaces

    # Page break indicator for text files
    PAGE_BREAK = "\n" + "=" * 60 + "\n" + "ANSWER KEY" + "\n" + "=" * 60 + "\n"

    def get_extension(self) -> str:
        return '.txt'

    def format(self, exam: ParsedExam, output_path: Union[str, Path],
               exam_type: ExamType = ExamType.FINAL) -> Path:
        """
        Format exam content into a plain text file.

        Args:
            exam: ParsedExam containing questions and answers
            output_path: Path for the output .txt file
            exam_type: Type of exam (practice or final)

        Returns:
            Path to the created text file
        """
        output_path = self.ensure_extension(output_path)

        lines = []

        # Add questions
        for question in exam.questions:
            lines.extend(self._format_question(question))

        # Add answer key section
        if exam.answers:
            lines.append(self.PAGE_BREAK)
            for answer in exam.answers:
                lines.append(self._format_answer(answer, exam_type))
                lines.append("")  # Blank line after each answer

        # Write to file
        content = "\n".join(lines)
        output_path.write_text(content, encoding='utf-8')

        return output_path

    def _format_question(self, question: Question) -> list[str]:
        """
        Format a question and its choices as text lines.

        Returns a list of lines with blank lines between each choice.
        """
        lines = []

        # Question text
        lines.append(f"{question.number}.\t{question.text}")
        lines.append("")  # Blank line after question text

        # Choices - each followed by a blank line
        for choice in question.choices:
            lines.append(f"{self.CHOICE_INDENT}{choice.letter}.\t{choice.text}")
            lines.append("")  # Blank line after each choice

        return lines

    def _format_answer(self, answer: Answer, exam_type: ExamType) -> str:
        """Format an answer key entry as a single line."""
        if exam_type == ExamType.PRACTICE:
            # Practice: "#.    <letter>    <code ref>"
            return f"{answer.question_number}.\t{answer.answer_letter}\t{answer.payload}"
        else:
            # Final: "#.    <letter>)    <source> (<citation>)"
            return f"{answer.question_number}.\t{answer.answer_letter})\t{answer.payload}"
