"""
PDF formatter using ReportLab.

Produces .pdf files with proper formatting matching the VBA macro specifications.
"""

from pathlib import Path
from typing import Union

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT

from .formatter import BaseFormatter, BODY_FONT, BODY_SIZE, MARGIN_INCHES, CHOICE_INDENT_INCHES
from .parser import ParsedExam, Question, Answer


class PDFFormatter(BaseFormatter):
    """
    Formatter that produces PDF documents using ReportLab.

    Applies formatting rules:
    - Times New Roman (Times-Roman in ReportLab), 12pt font
    - 0.5 inch margins
    - Questions formatted as "#.\\t<text>"
    - Choices indented 0.25 inches as "A.\\t<text>"
    - Answer key on a new page
    - MCQ blocks kept together (not split across pages)
    """

    # ReportLab font name for Times New Roman
    PDF_FONT = "Times-Roman"

    def get_extension(self) -> str:
        return '.pdf'

    def format(self, exam: ParsedExam, output_path: Union[str, Path]) -> Path:
        """
        Format exam content into a PDF document.

        Args:
            exam: ParsedExam containing questions and answers
            output_path: Path for the output .pdf file

        Returns:
            Path to the created PDF document
        """
        output_path = self.ensure_extension(output_path)

        # Create document with margins
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            topMargin=MARGIN_INCHES * inch,
            bottomMargin=MARGIN_INCHES * inch,
            leftMargin=MARGIN_INCHES * inch,
            rightMargin=MARGIN_INCHES * inch
        )

        # Create styles
        styles = self._create_styles()

        # Build content
        story = []

        # Add questions
        for question in exam.questions:
            question_block = self._create_question_block(question, styles)
            story.append(KeepTogether(question_block))

        # Add answer key on new page
        if exam.answers:
            story.append(PageBreak())
            for answer in exam.answers:
                answer_para = self._create_answer_paragraph(answer, styles)
                story.append(answer_para)
                story.append(Spacer(1, 12))

        doc.build(story)
        return output_path

    def _create_styles(self) -> dict:
        """Create paragraph styles for different content types."""
        styles = {}

        # Question style
        styles['question'] = ParagraphStyle(
            'Question',
            fontName=self.PDF_FONT,
            fontSize=BODY_SIZE,
            leading=BODY_SIZE * 1.2,  # Line spacing
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
            spaceAfter=0,
            leftIndent=CHOICE_INDENT_INCHES * inch,
            firstLineIndent=0,
        )

        # Last choice style (with space after)
        styles['choice_last'] = ParagraphStyle(
            'ChoiceLast',
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

    def _create_question_block(self, question: Question, styles: dict) -> list:
        """
        Create a list of flowables for a question and its choices.

        Returns a list that will be wrapped in KeepTogether.
        """
        block = []

        # Question text with tab simulation (using spaces)
        q_text = self._escape_text(f"{question.number}.    {question.text}")
        block.append(Paragraph(q_text, styles['question']))

        # Choices
        for i, choice in enumerate(question.choices):
            is_last = (i == len(question.choices) - 1)
            style = styles['choice_last'] if is_last else styles['choice']

            c_text = self._escape_text(f"{choice.letter}.    {choice.text}")
            block.append(Paragraph(c_text, style))

        return block

    def _create_answer_paragraph(self, answer: Answer, styles: dict) -> Paragraph:
        """Create a paragraph for an answer key entry."""
        # Format: "#.    A)    payload"
        a_text = self._escape_text(
            f"{answer.question_number}.    {answer.answer_letter})    {answer.payload}"
        )
        return Paragraph(a_text, styles['answer'])

    def _escape_text(self, text: str) -> str:
        """Escape special XML/HTML characters for ReportLab."""
        # ReportLab Paragraph uses XML-like markup
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text
