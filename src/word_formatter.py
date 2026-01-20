"""
Word document formatter using python-docx.

Produces .docx files with proper formatting matching the VBA macro specifications.
"""

from pathlib import Path
from typing import Union

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from .formatter import BaseFormatter, BODY_FONT, BODY_SIZE, MARGIN_INCHES, CHOICE_INDENT_INCHES
from .parser import ParsedExam, Question, Answer


class WordFormatter(BaseFormatter):
    """
    Formatter that produces Microsoft Word (.docx) documents.

    Applies formatting rules:
    - Times New Roman, 12pt font
    - 0.5 inch margins
    - Questions formatted as "#.\\t<text>"
    - Choices indented 0.25 inches as "A.\\t<text>"
    - Answer key on a new page
    - MCQ blocks kept together (not split across pages)
    """

    def get_extension(self) -> str:
        return '.docx'

    def format(self, exam: ParsedExam, output_path: Union[str, Path]) -> Path:
        """
        Format exam content into a Word document.

        Args:
            exam: ParsedExam containing questions and answers
            output_path: Path for the output .docx file

        Returns:
            Path to the created Word document
        """
        output_path = self.ensure_extension(output_path)

        doc = Document()
        self._setup_document(doc)

        # Add questions section
        for question in exam.questions:
            self._add_question(doc, question)

        # Add answer key on a new page (if there are answers)
        if exam.answers:
            self._add_page_break(doc)
            for answer in exam.answers:
                self._add_answer(doc, answer)

        doc.save(str(output_path))
        return output_path

    def _setup_document(self, doc: Document):
        """Configure document margins and default styles."""
        # Set margins
        for section in doc.sections:
            section.top_margin = Inches(MARGIN_INCHES)
            section.bottom_margin = Inches(MARGIN_INCHES)
            section.left_margin = Inches(MARGIN_INCHES)
            section.right_margin = Inches(MARGIN_INCHES)

        # Set default font
        style = doc.styles['Normal']
        font = style.font
        font.name = BODY_FONT
        font.size = Pt(BODY_SIZE)

        # Also set font for East Asian text
        style.element.rPr.rFonts.set(qn('w:eastAsia'), BODY_FONT)

    def _add_question(self, doc: Document, question: Question):
        """Add a question with its choices to the document."""
        # Add question text
        q_para = doc.add_paragraph()
        q_para.add_run(f"{question.number}.\t{question.text}")

        # Format question paragraph
        self._format_paragraph(q_para, 'question')

        # Add choices
        for i, choice in enumerate(question.choices):
            is_last = (i == len(question.choices) - 1)
            c_para = doc.add_paragraph()
            c_para.add_run(f"{choice.letter}.\t{choice.text}")

            choice_type = 'choice_last' if is_last else 'choice'
            self._format_paragraph(c_para, choice_type)

            # Set indentation for choices
            c_para.paragraph_format.left_indent = Inches(CHOICE_INDENT_INCHES)

    def _add_answer(self, doc: Document, answer: Answer):
        """Add an answer key entry to the document."""
        a_para = doc.add_paragraph()
        a_para.add_run(f"{answer.question_number}.\t{answer.answer_letter})\t{answer.payload}")

        self._format_paragraph(a_para, 'answer')

    def _format_paragraph(self, para, para_type: str):
        """
        Apply formatting to a paragraph based on its type.

        Types:
        - 'question': Question text (keep with next choice)
        - 'choice': Non-final choice (keep with next)
        - 'choice_last': Final choice (space after)
        - 'answer': Answer key entry
        """
        fmt = para.paragraph_format

        # Common settings
        fmt.space_before = Pt(0)
        fmt.line_spacing = 1.0  # Single spacing
        fmt.alignment = WD_ALIGN_PARAGRAPH.LEFT
        fmt.left_indent = Pt(0)
        fmt.first_line_indent = Pt(0)

        # Set font
        for run in para.runs:
            run.font.name = BODY_FONT
            run.font.size = Pt(BODY_SIZE)
            run.font.bold = False

        if para_type == 'question':
            fmt.space_after = Pt(12)  # Blank line after question text
            self._set_keep_together(para, True)
            self._set_keep_with_next(para, True)

        elif para_type == 'choice':
            fmt.space_after = Pt(0)
            self._set_keep_together(para, True)
            self._set_keep_with_next(para, True)

        elif para_type == 'choice_last':
            fmt.space_after = Pt(12)  # Blank line after last choice
            self._set_keep_together(para, True)
            self._set_keep_with_next(para, False)

        elif para_type == 'answer':
            fmt.space_after = Pt(12)
            self._set_keep_together(para, True)
            self._set_keep_with_next(para, False)

    def _set_keep_together(self, para, value: bool):
        """Set paragraph keep-together property using XML."""
        pPr = para._element.get_or_add_pPr()
        keep_lines = pPr.find(qn('w:keepLines'))

        if value:
            if keep_lines is None:
                keep_lines = OxmlElement('w:keepLines')
                pPr.append(keep_lines)
        else:
            if keep_lines is not None:
                pPr.remove(keep_lines)

    def _set_keep_with_next(self, para, value: bool):
        """Set paragraph keep-with-next property using XML."""
        pPr = para._element.get_or_add_pPr()
        keep_next = pPr.find(qn('w:keepNext'))

        if value:
            if keep_next is None:
                keep_next = OxmlElement('w:keepNext')
                pPr.append(keep_next)
        else:
            if keep_next is not None:
                pPr.remove(keep_next)

    def _add_page_break(self, doc: Document):
        """Add a page break before the answer key."""
        doc.add_page_break()
