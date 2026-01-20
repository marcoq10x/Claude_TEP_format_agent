#!/usr/bin/env python3
"""
LLM Output Formatter - CLI Application

Formats exam content from LLM outputs into Word, PDF, or TXT files.

Usage:
    python -m src.main input.txt -o output.docx
    python -m src.main input.txt -o output.pdf
    python -m src.main input.txt -o output.txt
    echo "Q1. Question? A. a B. b C. c D. d" | python -m src.main - -o output.docx
"""

import sys
from pathlib import Path
from typing import Optional

import click

from .parser import ExamParser
from .word_formatter import WordFormatter
from .pdf_formatter import PDFFormatter
from .txt_formatter import TxtFormatter


def get_formatter(output_format: str):
    """Get the appropriate formatter based on output format."""
    formatters = {
        'docx': WordFormatter,
        'word': WordFormatter,
        'pdf': PDFFormatter,
        'txt': TxtFormatter,
        'text': TxtFormatter,
    }

    fmt_lower = output_format.lower()
    if fmt_lower not in formatters:
        raise ValueError(
            f"Unsupported format: {output_format}. "
            f"Supported formats: docx, pdf, txt"
        )

    return formatters[fmt_lower]()


def detect_format_from_path(path: Path) -> str:
    """Detect output format from file extension."""
    ext = path.suffix.lower()
    format_map = {
        '.docx': 'docx',
        '.doc': 'docx',
        '.pdf': 'pdf',
        '.txt': 'txt',
    }

    if ext in format_map:
        return format_map[ext]

    return 'docx'  # Default to Word


@click.command()
@click.argument('input_file', type=click.Path(exists=False))
@click.option(
    '-o', '--output',
    type=click.Path(),
    help='Output file path. Format detected from extension (.docx, .pdf, .txt)'
)
@click.option(
    '-f', '--format',
    'output_format',
    type=click.Choice(['docx', 'pdf', 'txt'], case_sensitive=False),
    help='Output format (overrides extension detection)'
)
@click.option(
    '--stdin', '-',
    'use_stdin',
    is_flag=True,
    help='Read input from stdin instead of file'
)
def main(input_file: str, output: Optional[str], output_format: Optional[str], use_stdin: bool):
    """
    Format LLM output into Word, PDF, or TXT documents.

    INPUT_FILE is the path to the input text file, or use '-' for stdin.

    Examples:

        # Convert text file to Word document
        python -m src.main exam.txt -o exam.docx

        # Convert to PDF
        python -m src.main exam.txt -o exam.pdf

        # Convert to plain text (reformatted)
        python -m src.main exam.txt -o exam_formatted.txt

        # Read from stdin
        echo "Q1. Question? A. a B. b C. c D. d" | python -m src.main - -o output.docx
    """
    # Read input
    if input_file == '-' or use_stdin:
        click.echo("Reading from stdin...", err=True)
        input_text = sys.stdin.read()
        if not output:
            click.echo("Error: Output file required when reading from stdin", err=True)
            sys.exit(1)
    else:
        input_path = Path(input_file)
        if not input_path.exists():
            click.echo(f"Error: Input file not found: {input_file}", err=True)
            sys.exit(1)

        click.echo(f"Reading from: {input_path}", err=True)
        input_text = input_path.read_text(encoding='utf-8')

        # Default output path if not specified
        if not output:
            output = input_path.stem + '_formatted.docx'

    output_path = Path(output)

    # Determine format
    if output_format:
        fmt = output_format
    else:
        fmt = detect_format_from_path(output_path)

    click.echo(f"Output format: {fmt.upper()}", err=True)

    # Parse input
    parser = ExamParser()
    try:
        exam = parser.parse(input_text)
    except Exception as e:
        click.echo(f"Error parsing input: {e}", err=True)
        sys.exit(1)

    click.echo(
        f"Parsed: {len(exam.questions)} questions, {len(exam.answers)} answers",
        err=True
    )

    if not exam.questions and not exam.answers:
        click.echo("Warning: No questions or answers found in input", err=True)

    # Format output
    try:
        formatter = get_formatter(fmt)
        result_path = formatter.format(exam, output_path)
        click.echo(f"Created: {result_path}", err=True)
    except Exception as e:
        click.echo(f"Error formatting output: {e}", err=True)
        sys.exit(1)


def format_text(
    text: str,
    output_path: str,
    output_format: Optional[str] = None
) -> Path:
    """
    Programmatic API to format text.

    Args:
        text: Raw exam text from LLM output
        output_path: Path for output file
        output_format: Optional format override ('docx', 'pdf', 'txt')

    Returns:
        Path to created file
    """
    path = Path(output_path)

    if output_format:
        fmt = output_format
    else:
        fmt = detect_format_from_path(path)

    parser = ExamParser()
    exam = parser.parse(text)

    formatter = get_formatter(fmt)
    return formatter.format(exam, path)


if __name__ == '__main__':
    main()
