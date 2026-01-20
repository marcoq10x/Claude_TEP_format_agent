"""
Base formatter class defining the interface for all output formatters.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

from .parser import ParsedExam


# Formatting constants (matching VBA code)
BODY_FONT = "Times New Roman"
BODY_SIZE = 12  # points
MARGIN_INCHES = 0.5
CHOICE_INDENT_INCHES = 0.25
BLANK_LINE_PTS = 12  # approximately one blank line at 12pt single spacing


class BaseFormatter(ABC):
    """
    Abstract base class for exam document formatters.

    Subclasses must implement the format() method to produce
    output in their specific format (Word, PDF, TXT).
    """

    def __init__(self):
        self.font_name = BODY_FONT
        self.font_size = BODY_SIZE
        self.margin = MARGIN_INCHES
        self.choice_indent = CHOICE_INDENT_INCHES

    @abstractmethod
    def format(self, exam: ParsedExam, output_path: Union[str, Path]) -> Path:
        """
        Format the parsed exam content and save to a file.

        Args:
            exam: ParsedExam containing questions and answers
            output_path: Path where the output file should be saved

        Returns:
            Path to the created file
        """
        pass

    @abstractmethod
    def get_extension(self) -> str:
        """Return the file extension for this format (e.g., '.docx')."""
        pass

    def ensure_extension(self, path: Union[str, Path]) -> Path:
        """Ensure the output path has the correct extension."""
        path = Path(path)
        ext = self.get_extension()
        if path.suffix.lower() != ext.lower():
            path = path.with_suffix(ext)
        return path
