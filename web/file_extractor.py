"""
Text extraction utilities for various file formats.
Supports: TXT, DOCX, PDF, CSV, RTF
"""

import io
import csv
from pathlib import Path


def extract_text_from_txt(file_content: bytes) -> str:
    """Extract text from a plain text file."""
    # Try common encodings
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
        try:
            return file_content.decode(encoding)
        except UnicodeDecodeError:
            continue
    # Fallback with replacement
    return file_content.decode('utf-8', errors='replace')


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from a Word DOCX file."""
    from docx import Document

    doc = Document(io.BytesIO(file_content))
    paragraphs = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)

    return '\n'.join(paragraphs)


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from a PDF file."""
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(file_content))
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    return '\n'.join(text_parts)


def extract_text_from_csv(file_content: bytes) -> str:
    """Extract text from a CSV file, preserving structure."""
    text = extract_text_from_txt(file_content)

    # Parse CSV and reconstruct as readable text
    lines = []
    try:
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            # Join cells with tabs for readability
            lines.append('\t'.join(row))
    except csv.Error:
        # If CSV parsing fails, return as plain text
        return text

    return '\n'.join(lines)


def extract_text_from_rtf(file_content: bytes) -> str:
    """Extract text from an RTF file."""
    from striprtf.striprtf import rtf_to_text

    # Decode RTF content
    rtf_text = extract_text_from_txt(file_content)

    # Strip RTF formatting
    return rtf_to_text(rtf_text)


def extract_text(filename: str, file_content: bytes) -> str:
    """
    Extract text from a file based on its extension.

    Args:
        filename: Original filename (used to determine format)
        file_content: Raw file content as bytes

    Returns:
        Extracted text content

    Raises:
        ValueError: If file format is not supported
    """
    ext = Path(filename).suffix.lower()

    extractors = {
        '.txt': extract_text_from_txt,
        '.docx': extract_text_from_docx,
        '.pdf': extract_text_from_pdf,
        '.csv': extract_text_from_csv,
        '.rtf': extract_text_from_rtf,
    }

    if ext not in extractors:
        supported = ', '.join(extractors.keys())
        raise ValueError(f"Unsupported file format: {ext}. Supported formats: {supported}")

    return extractors[ext](file_content)


# Supported file extensions for upload
SUPPORTED_EXTENSIONS = {'.txt', '.docx', '.pdf', '.csv', '.rtf'}

def is_supported_file(filename: str) -> bool:
    """Check if a file extension is supported."""
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS
