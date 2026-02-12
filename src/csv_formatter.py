"""
CSV formatter.

Produces .csv files with exam content in tabular format.
"""

import csv
from pathlib import Path
from typing import Union

from .formatter import BaseFormatter, ExamType
from .parser import ParsedExam, Question, Answer


class CSVFormatter(BaseFormatter):
    """
    Formatter that produces CSV (.csv) files.

    Generates two sections in the CSV:
    - Questions section with columns: Number, Question, A, B, C, D
    - Answer Key section with columns: Number, Answer, Explanation
    """

    def get_extension(self) -> str:
        return '.csv'

    def format(self, exam: ParsedExam, output_path: Union[str, Path],
               exam_type: ExamType = ExamType.FINAL) -> Path:
        output_path = self.ensure_extension(output_path)

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            title = exam.title or "Exam"

            # Write title
            writer.writerow([title])
            writer.writerow([])

            # Questions section header
            writer.writerow(['QUESTIONS'])
            writer.writerow(['Number', 'Question', 'A', 'B', 'C', 'D'])

            # Write questions
            for question in exam.questions:
                row = self._format_question_row(question)
                writer.writerow(row)

            # Blank row separator
            writer.writerow([])

            # Answer key section
            if exam.answers:
                writer.writerow(['ANSWER KEY'])
                writer.writerow(['Number', 'Answer', 'Explanation'])

                for answer in exam.answers:
                    row = self._format_answer_row(answer, exam_type)
                    writer.writerow(row)

        return output_path

    def _format_question_row(self, question: Question) -> list[str]:
        """Format a question as a CSV row."""
        row = [str(question.number), question.text]

        # Add choices A, B, C, D (pad with empty if missing)
        choice_dict = {c.letter.upper(): c.text for c in question.choices}
        for letter in ['A', 'B', 'C', 'D']:
            row.append(choice_dict.get(letter, ''))

        return row

    def _format_answer_row(self, answer: Answer, exam_type: ExamType) -> list[str]:
        """Format an answer as a CSV row."""
        if exam_type == ExamType.PRACTICE:
            return [str(answer.question_number), answer.answer_letter, answer.payload]
        else:
            return [str(answer.question_number), f"{answer.answer_letter})", answer.payload]
