"""
Plain text formatter.

Produces .txt files with clean formatting for exam content.
"""

from pathlib import Path
from typing import Union

from .formatter import BaseFormatter
from .parser import ParsedExam, Question, Answer


class TxtFormatter(BaseFormatter):
    """
    Formatter that produces plain text (.txt) files.

    Applies formatting rules:
    - Questions formatted as "#.\\t<text>"
    - Choices indented with spaces as "    A.\\t<text>"
    - Blank line between questions
    - Page break indicator before answer key
    - Answer entries formatted as "#.\\tA)\\t<payload>"
    """

    # Number of spaces for choice indentation (simulating 0.25 inch)
    CHOICE_INDENT = "    "  # 4 spaces

    # Page break indicator for text files
    PAGE_BREAK = "\n" + "=" * 60 + "\n" + "ANSWER KEY" + "\n" + "=" * 60 + "\n"

    def get_extension(self) -> str:
        return '.txt'

    def format(self, exam: ParsedExam, output_path: Union[str, Path]) -> Path:
        """
        Format exam content into a plain text file.

        Args:
            exam: ParsedExam containing questions and answers
            output_path: Path for the output .txt file

        Returns:
            Path to the created text file
        """
        output_path = self.ensure_extension(output_path)

        lines = []

        # Add questions
        for i, question in enumerate(exam.questions):
            lines.extend(self._format_question(question))

            # Add blank line between questions (but not after last)
            if i < len(exam.questions) - 1:
                lines.append("")

        # Add answer key section
        if exam.answers:
            lines.append(self.PAGE_BREAK)
            for answer in exam.answers:
                lines.append(self._format_answer(answer))
                lines.append("")  # Blank line after each answer

        # Write to file
        content = "\n".join(lines)
        output_path.write_text(content, encoding='utf-8')

        return output_path

    def _format_question(self, question: Question) -> list[str]:
        """
        Format a question and its choices as text lines.

        Returns a list of lines.
        """
        lines = []

        # Question text
        lines.append(f"{question.number}.\t{question.text}")
        lines.append("")  # Blank line after question text

        # Choices
        for choice in question.choices:
            lines.append(f"{self.CHOICE_INDENT}{choice.letter}.\t{choice.text}")

        return lines

    def _format_answer(self, answer: Answer) -> str:
        """Format an answer key entry as a single line."""
        return f"{answer.question_number}.\t{answer.answer_letter})\t{answer.payload}"
