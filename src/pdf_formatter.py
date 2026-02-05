"""
PDF formatter using ReportLab.

Produces .pdf files with proper formatting matching the VBA macro specifications.
"""

from pathlib import Path
from typing import Union

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from .formatter import BaseFormatter, ExamType, BODY_FONT, BODY_SIZE, MARGIN_INCHES, CHOICE_INDENT_INCHES
from .parser import ParsedExam, Question, Answer


class PDFFormatter(BaseFormatter):
    """
    Formatter that produces PDF documents using ReportLab.

    Applies formatting rules:
    - Times New Roman (Times-Roman in ReportLab), 12pt font
    - 0.5 inch margins
    - 2-line centered bold 20pt header (Title + section name)
    - Questions formatted as "#.    <text>"
    - Entire question block kept together on same page
    - Choices each on own line with blank line after each
    - Answer key on a new page
    - Practice exam answers: "#.    <letter>    <code ref>"
    - Final exam answers: "#.    <letter>)    <source> (<citation>)"
    """

    PDF_FONT = "Times-Roman"
    PDF_FONT_BOLD = "Times-Bold"

    def get_extension(self) -> str:
        return '.pdf'

    def format(self, exam: ParsedExam, output_path: Union[str, Path],
               exam_type: ExamType = ExamType.FINAL) -> Path:
        output_path = self.ensure_extension(output_path)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            topMargin=MARGIN_INCHES * inch,
            bottomMargin=MARGIN_INCHES * inch,
            leftMargin=MARGIN_INCHES * inch,
            rightMargin=MARGIN_INCHES * inch
        )

        styles = self._create_styles()
        story = []

        title = exam.title or "Exam"

        # Questions header
        story.extend(self._create_header(title, "Questions", styles))

        # Add questions (each wrapped in KeepTogether)
        for question in exam.questions:
            question_block = self._create_question_block(question, styles)
            story.append(KeepTogether(question_block))

        # Answer key on new page
        if exam.answers:
            story.append(PageBreak())
            story.extend(self._create_header(title, "Answer Key", styles))
            for answer in exam.answers:
                answer_para = self._create_answer_paragraph(answer, styles, exam_type)
                story.append(answer_para)
                story.append(Spacer(1, 12))

        doc.build(story)
        return output_path

    def _create_styles(self) -> dict:
        """Create paragraph styles for different content types."""
        styles = {}

        # Header style - centered, bold, 20pt
        styles['header'] = ParagraphStyle(
            'Header',
            fontName=self.PDF_FONT_BOLD,
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=0,
        )

        # Header last line (with space after)
        styles['header_last'] = ParagraphStyle(
            'HeaderLast',
            fontName=self.PDF_FONT_BOLD,
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=24,
        )

        # Question style
        styles['question'] = ParagraphStyle(
            'Question',
            fontName=self.PDF_FONT,
            fontSize=BODY_SIZE,
            leading=BODY_SIZE * 1.2,
            alignment=TA_LEFT,
            spaceAfter=12,
            leftIndent=0,
            firstLineIndent=0,
        )

        # Choice style (indented)
        styles['choice'] = ParagraphStyle(
            'Choice',
            fontName=self.PDF_FONT,
            fontSize=BODY_SIZE,
            leading=BODY_SIZE * 1.2,
            alignment=TA_LEFT,
            spaceAfter=12,
            leftIndent=CHOICE_INDENT_INCHES * inch,
            firstLineIndent=0,
        )

        # Answer style
        styles['answer'] = ParagraphStyle(
            'Answer',
            fontName=self.PDF_FONT,
            fontSize=BODY_SIZE,
            leading=BODY_SIZE * 1.2,
            alignment=TA_LEFT,
            spaceAfter=12,
            leftIndent=0,
            firstLineIndent=0,
        )

        return styles

    def _create_header(self, title: str, section_name: str, styles: dict) -> list:
        """Create 2-line centered bold 20pt header flowables."""
        return [
            Paragraph(self._escape_text(title), styles['header']),
            Paragraph(self._escape_text(section_name), styles['header_last']),
        ]

    def _create_question_block(self, question: Question, styles: dict) -> list:
        """Create a list of flowables for a question and its choices."""
        block = []

        q_text = self._escape_text(f"{question.number}.    {question.text}")
        block.append(Paragraph(q_text, styles['question']))

        for choice in question.choices:
            c_text = self._escape_text(f"{choice.letter}.    {choice.text}")
            block.append(Paragraph(c_text, styles['choice']))

        return block

    def _create_answer_paragraph(self, answer: Answer, styles: dict,
                                  exam_type: ExamType) -> Paragraph:
        """Create a paragraph for an answer key entry."""
        if exam_type == ExamType.PRACTICE:
            a_text = self._escape_text(
                f"{answer.question_number}.    {answer.answer_letter}    {answer.payload}"
            )
        else:
            a_text = self._escape_text(
                f"{answer.question_number}.    {answer.answer_letter})    {answer.payload}"
            )
        return Paragraph(a_text, styles['answer'])

    def _escape_text(self, text: str) -> str:
        """Escape special XML/HTML characters for ReportLab."""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text
