"""
File text extractor module.

Extracts plain text content from various file formats:
- TXT: Plain text (direct read)
- DOCX: Microsoft Word documents (via python-docx)
- PDF: PDF documents (via PyPDF2)
- CSV: Comma-separated values (via csv module)
- RTF: Rich Text Format (via striprtf)
"""

import csv
import io
from pathlib import Path


def extract_text(file_path: str, original_filename: str = None) -> str:
    """
    Extract text content from a file based on its extension.

    Args:
        file_path: Path to the uploaded file on disk.
        original_filename: The original filename (used to detect type).

    Returns:
        Extracted plain text content.

    Raises:
        ValueError: If the file type is unsupported.
    """
    if original_filename:
        ext = Path(original_filename).suffix.lower()
    else:
        ext = Path(file_path).suffix.lower()

    extractors = {
        '.txt': _extract_txt,
        '.docx': _extract_docx,
        '.pdf': _extract_pdf,
        '.csv': _extract_csv,
        '.rtf': _extract_rtf,
    }

    if ext not in extractors:
        raise ValueError(f"Unsupported file type: {ext}")

    return extractors[ext](file_path)


def _extract_txt(file_path: str) -> str:
    """Extract text from a plain text file."""
    # Try UTF-8 first, fall back to latin-1
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.read()


def _extract_docx(file_path: str) -> str:
    """Extract text from a Microsoft Word (.docx) document."""
    from docx import Document

    doc = Document(file_path)
    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)
    return '\n'.join(paragraphs)


def _extract_pdf(file_path: str) -> str:
    """Extract text from a PDF document."""
    from PyPDF2 import PdfReader

    reader = PdfReader(file_path)
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text.strip())
    return '\n'.join(pages_text)


def _extract_csv(file_path: str) -> str:
    """Extract text from a CSV file by joining all cells."""
    lines = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                line = ' '.join(cell.strip() for cell in row if cell.strip())
                if line:
                    lines.append(line)
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            reader = csv.reader(f)
            for row in reader:
                line = ' '.join(cell.strip() for cell in row if cell.strip())
                if line:
                    lines.append(line)
    return '\n'.join(lines)


def _extract_rtf(file_path: str) -> str:
    """Extract text from an RTF file."""
    from striprtf.striprtf import rtf_to_text

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            rtf_content = f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            rtf_content = f.read()

    return rtf_to_text(rtf_content)


# Supported extensions for validation
SUPPORTED_EXTENSIONS = {'.txt', '.docx', '.pdf', '.csv', '.rtf'}


def is_supported(filename: str) -> bool:
    """Check if a filename has a supported extension."""
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS
