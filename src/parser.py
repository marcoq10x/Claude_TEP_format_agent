"""
Parser module for extracting exam questions, choices, and answers from LLM output.

This parser handles various input formats and normalizes them into a structured format
suitable for formatting into Word, PDF, or TXT documents.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ContentType(Enum):
    """Types of content in exam documents."""
    QUESTION = "Q"
    CHOICE_NEXT = "C_NEXT"
    CHOICE_LAST = "C_LAST"
    ANSWER = "A"


@dataclass
class Choice:
    """Represents a multiple choice option."""
    letter: str  # A, B, C, or D
    text: str


@dataclass
class Question:
    """Represents an exam question with its choices."""
    number: int
    text: str
    choices: list[Choice] = field(default_factory=list)


@dataclass
class Answer:
    """Represents an answer key entry."""
    question_number: int
    answer_letter: str
    payload: str  # Citation or explanation


@dataclass
class ParsedExam:
    """Contains all parsed exam content."""
    questions: list[Question] = field(default_factory=list)
    answers: list[Answer] = field(default_factory=list)

    @property
    def is_balanced(self) -> bool:
        """Check if question and answer counts match (1:1 ratio)."""
        return len(self.questions) == len(self.answers)

    @property
    def mismatch_info(self) -> str:
        """Return info about any question/answer count mismatch."""
        q_count = len(self.questions)
        a_count = len(self.answers)
        if q_count == a_count:
            return ""
        return (f"Mismatch: {q_count} questions but {a_count} answers. "
                f"Expected 1:1 ratio.")


class ExamParser:
    """
    Parser that extracts exam questions, choices, and answer keys from text.

    Handles various input formats from LLM outputs and normalizes them
    into a structured format.
    """

    # Pattern to match question numbers like "Q1.", "1.", "Q1)", "1)"
    QUESTION_PATTERN = re.compile(
        r'^[Qq]?(\d+)[.):]\s*(.*)$'
    )

    # Pattern to match choice markers like "A.", "A)", "a.", "a)"
    CHOICE_PATTERN = re.compile(
        r'^([A-Da-d])[.)]\s*(.*)$'
    )

    # Pattern to find inline choices: "A. text B. text C. text D. text"
    INLINE_CHOICES_PATTERN = re.compile(
        r'([A-Da-d])[.)]\s*([^A-Da-d]*?)(?=\s+[A-Da-d][.)]|$)',
        re.IGNORECASE
    )

    # Pattern for answer key entries like "Q1 A) explanation" or "1. B. text"
    ANSWER_PATTERN = re.compile(
        r'[Qq]?(\d+)[.):]*\s*["\']?([A-Da-d])[.)"]?\s*(.*)',
        re.IGNORECASE
    )

    def __init__(self):
        self.mode = "questions"  # "questions" or "answers"

    def parse(self, text: str) -> ParsedExam:
        """
        Parse raw text into structured exam content.

        Args:
            text: Raw text containing exam questions and/or answers

        Returns:
            ParsedExam with parsed questions and answers
        """
        result = ParsedExam()
        self.mode = "questions"

        # Normalize text
        text = self._normalize_text(text)
        lines = text.split('\n')

        current_question: Optional[Question] = None
        pending_choices: list[Choice] = []

        for line in lines:
            line = self._clean_line(line)
            if not line:
                continue

            # Check for Answer Key section header
            if self._is_answer_key_header(line):
                # Save any pending question
                if current_question:
                    current_question.choices = pending_choices
                    result.questions.append(current_question)
                    current_question = None
                    pending_choices = []
                self.mode = "answers"
                continue

            # Auto-detect answer mode from content
            if self.mode == "questions" and self._looks_like_answer_chunk(line):
                # Save any pending question
                if current_question:
                    current_question.choices = pending_choices
                    result.questions.append(current_question)
                    current_question = None
                    pending_choices = []
                self.mode = "answers"

            if self.mode == "questions":
                processed = self._process_question_line(
                    line, current_question, pending_choices, result
                )
                current_question = processed[0]
                pending_choices = processed[1]
            else:
                self._process_answer_line(line, result)

        # Save any remaining question
        if current_question:
            current_question.choices = pending_choices
            result.questions.append(current_question)

        return result

    def _normalize_text(self, text: str) -> str:
        """Normalize various text encodings and line endings."""
        # Replace smart quotes with regular quotes
        text = text.replace('\u201c', '"')  # Left double quote
        text = text.replace('\u201d', '"')  # Right double quote
        text = text.replace('\u2018', "'")  # Left single quote
        text = text.replace('\u2019', "'")  # Right single quote

        # Normalize line endings
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        text = text.replace('\x0b', '\n')  # Vertical tab
        text = text.replace('\x0c', '\n')  # Form feed

        return text

    def _clean_line(self, line: str) -> str:
        """Clean a single line of text."""
        # Replace tabs and non-breaking spaces with regular spaces
        line = line.replace('\t', ' ')
        line = line.replace('\xa0', ' ')  # Non-breaking space

        # Collapse multiple spaces
        while '  ' in line:
            line = line.replace('  ', ' ')

        return line.strip()

    def _is_answer_key_header(self, line: str) -> bool:
        """Check if line is an answer key section header."""
        return 'answer key' in line.lower()

    def _looks_like_answer_chunk(self, line: str) -> bool:
        """
        Detect if a line looks like an answer entry rather than a question.

        Answer entries typically have patterns like:
        - Q1 A) with citation/page reference
        - Contains "Answer/Citation" label
        - Has page reference along with answer letter
        """
        upper = line.upper()

        # Check for explicit Answer/Citation marker
        if 'ANSWER/CITATION' in upper:
            return True

        # Check for Q# pattern with answer letter and page reference
        if upper.startswith('Q') or (upper and upper[0].isdigit()):
            has_answer_letter = any(
                f'{letter})' in upper or f'{letter}.' in upper
                for letter in 'ABCD'
            )
            has_page_ref = 'PAGE' in upper or '(P' in upper or ' P.' in upper

            if has_answer_letter and has_page_ref:
                return True

        return False

    def _process_question_line(
        self,
        line: str,
        current_question: Optional[Question],
        pending_choices: list[Choice],
        result: ParsedExam
    ) -> tuple[Optional[Question], list[Choice]]:
        """
        Process a line in question mode.

        Returns updated current_question and pending_choices.
        """
        # Try to parse as a new question
        q_match = self.QUESTION_PATTERN.match(line)
        if q_match:
            # Save previous question if exists
            if current_question:
                current_question.choices = pending_choices
                result.questions.append(current_question)

            q_num = int(q_match.group(1))
            remainder = q_match.group(2).strip()

            # Check if choices are inline with question
            q_text, inline_choices = self._split_question_and_choices(remainder)

            current_question = Question(number=q_num, text=q_text)
            pending_choices = inline_choices

            return current_question, pending_choices

        # Try to parse as a choice line
        c_match = self.CHOICE_PATTERN.match(line)
        if c_match:
            letter = c_match.group(1).upper()
            text = c_match.group(2).strip()
            pending_choices.append(Choice(letter=letter, text=text))
            return current_question, pending_choices

        # Try to parse inline choices
        inline_choices = self._parse_inline_choices(line)
        if len(inline_choices) == 4:  # All four choices found
            pending_choices = inline_choices
            return current_question, pending_choices

        # Continuation of previous question text
        if current_question and not pending_choices:
            current_question.text += ' ' + line

        return current_question, pending_choices

    def _split_question_and_choices(self, text: str) -> tuple[str, list[Choice]]:
        """
        Split question text from inline choices if present.

        Returns (question_text, list_of_choices).
        """
        # Find first choice marker position
        first_choice_pos = self._find_first_choice_marker(text)

        if first_choice_pos == -1:
            return text, []

        q_text = text[:first_choice_pos].strip()
        choice_blob = text[first_choice_pos:]

        choices = self._parse_inline_choices(choice_blob)
        return q_text, choices

    def _find_first_choice_marker(self, text: str) -> int:
        """Find position of first choice marker (A. or A))."""
        for i, char in enumerate(text):
            if char.upper() == 'A':
                # Check if followed by . or )
                if i + 1 < len(text) and text[i + 1] in '.)':
                    # Check if preceded by space or at start
                    if i == 0 or text[i - 1] == ' ':
                        return i
        return -1

    def _parse_inline_choices(self, text: str) -> list[Choice]:
        """Parse choices that are all on one line."""
        choices = []

        # Find positions of all choice markers
        positions = {}
        for i, char in enumerate(text):
            if char.upper() in 'ABCD':
                if i + 1 < len(text) and text[i + 1] in '.)':
                    if i == 0 or text[i - 1] == ' ':
                        letter = char.upper()
                        if letter not in positions:
                            positions[letter] = i

        # Need all four choices in order
        if not all(letter in positions for letter in 'ABCD'):
            return []

        if not (positions['A'] < positions['B'] < positions['C'] < positions['D']):
            return []

        # Extract text for each choice
        for letter in 'ABCD':
            start = positions[letter] + 2  # Skip letter and delimiter

            # Find end position
            if letter == 'D':
                choice_text = text[start:].strip()
            else:
                next_letter = chr(ord(letter) + 1)
                end = positions[next_letter]
                choice_text = text[start:end].strip()

            choices.append(Choice(letter=letter, text=choice_text))

        return choices

    def _process_answer_line(self, line: str, result: ParsedExam):
        """Process a line in answer key mode."""
        # Try to split multiple answer chunks on one line
        chunks = self._split_answer_chunks(line)

        if not chunks:
            chunks = [line]

        for chunk in chunks:
            answer = self._parse_answer_chunk(chunk)
            if answer:
                result.answers.append(answer)

    def _split_answer_chunks(self, line: str) -> list[str]:
        """Split a line that may contain multiple Q# answers."""
        chunks = []

        # Find all Q# token positions
        positions = []
        for i, char in enumerate(line):
            if char.upper() == 'Q':
                if i + 1 < len(line) and line[i + 1].isdigit():
                    positions.append(i)

        if len(positions) <= 1:
            return []

        # Split at each position
        for i, pos in enumerate(positions):
            if i + 1 < len(positions):
                chunks.append(line[pos:positions[i + 1]].strip())
            else:
                chunks.append(line[pos:].strip())

        return chunks

    def _parse_answer_chunk(self, chunk: str) -> Optional[Answer]:
        """Parse a single answer entry."""
        chunk = self._clean_line(chunk)
        if not chunk:
            return None

        # Normalize quotes
        chunk = chunk.replace('\u201c', '"').replace('\u201d', '"')
        chunk = chunk.replace('\u2018', "'").replace('\u2019', "'")

        # Extract question number
        q_num = self._extract_question_number(chunk)
        if q_num is None:
            return None

        # Extract answer letter
        ans_letter = self._extract_answer_letter(chunk)
        if not ans_letter:
            return None

        # Extract payload (citation/explanation)
        payload = self._extract_payload(chunk, ans_letter)

        return Answer(
            question_number=q_num,
            answer_letter=ans_letter,
            payload=payload
        )

    def _extract_question_number(self, text: str) -> Optional[int]:
        """Extract question number from answer text."""
        # Skip leading Q if present
        start = 0
        if text and text[0].upper() == 'Q':
            start = 1

        # Extract digits
        num_str = ''
        for char in text[start:]:
            if char.isdigit():
                num_str += char
            else:
                break

        if num_str:
            return int(num_str)
        return None

    def _extract_answer_letter(self, text: str) -> str:
        """Extract answer letter (A, B, C, or D) from text."""
        # First check for quoted answer
        quoted = self._extract_quoted_text(text)
        if quoted:
            letter = self._parse_answer_from_quoted(quoted)
            if letter:
                return letter

        # Look for pattern like "A)" or "A." anywhere in text
        for i, char in enumerate(text):
            if char.upper() in 'ABCD':
                if i + 1 < len(text) and text[i + 1] in '.)':
                    return char.upper()

        return ''

    def _extract_quoted_text(self, text: str) -> str:
        """Extract first quoted segment from text."""
        start = text.find('"')
        if start == -1:
            return ''
        end = text.find('"', start + 1)
        if end == -1:
            return ''
        return text[start + 1:end]

    def _parse_answer_from_quoted(self, quoted: str) -> str:
        """Parse answer letter from quoted text."""
        quoted = quoted.strip()
        if not quoted:
            return ''

        # Single letter answer
        if len(quoted) == 1 and quoted.upper() in 'ABCD':
            return quoted.upper()

        # Letter followed by delimiter
        if len(quoted) >= 2:
            if quoted[0].upper() in 'ABCD' and quoted[1] in '.)':
                return quoted[0].upper()

        return ''

    def _extract_payload(self, text: str, ans_letter: str) -> str:
        """Extract the payload/citation from answer text."""
        # Remove quoted segment
        text = self._remove_quoted_segment(text)

        # Remove question number prefix
        text = self._strip_question_prefix(text)

        # Remove leading answer marker
        text = self._strip_answer_marker(text, ans_letter)

        # Check for Answer/Citation label
        ac_pos = text.upper().find('ANSWER/CITATION')
        if ac_pos != -1:
            before = text[:ac_pos].strip()
            after = text[ac_pos:].strip()

            # Normalize the Answer/Citation label
            after = self._normalize_citation_label(after)
            before = self._strip_answer_marker(before, ans_letter)

            if before:
                return f"{before} {after}".strip()
            return after

        # Extract page citation
        citation = self._extract_citation(text)
        if not citation:
            citation = self._find_page_reference(text)
        if not citation:
            citation = '?'

        # Clean up remainder
        remainder = self._remove_citation_from_text(text)
        remainder = self._strip_answer_marker(remainder, ans_letter)

        citation_part = f"Answer/Citation: {citation}"

        if remainder:
            return f"{remainder} {citation_part}".strip()
        return citation_part

    def _remove_quoted_segment(self, text: str) -> str:
        """Remove first quoted segment from text."""
        start = text.find('"')
        if start == -1:
            return text
        end = text.find('"', start + 1)
        if end == -1:
            return text
        return (text[:start] + ' ' + text[end + 1:]).strip()

    def _strip_question_prefix(self, text: str) -> str:
        """Remove leading Q# pattern from text."""
        text = text.strip()
        if not text:
            return ''

        start = 0
        if text[0].upper() == 'Q':
            start = 1

        # Skip digits
        while start < len(text) and text[start].isdigit():
            start += 1

        # Skip delimiters
        while start < len(text) and text[start] in '.):: ':
            start += 1

        return text[start:].strip()

    def _strip_answer_marker(self, text: str, ans_letter: str) -> str:
        """Remove leading answer marker like 'A)' or 'A.' from text."""
        text = text.strip()
        if not text:
            return ''

        if text[0].upper() == ans_letter.upper():
            if len(text) >= 2 and text[1] in '.)':
                return text[2:].strip()

        return text

    def _normalize_citation_label(self, text: str) -> str:
        """Normalize Answer/Citation label format."""
        text = text.strip()
        if not text:
            return 'Answer/Citation: ?'

        upper = text.upper()
        if upper.startswith('ANSWER/CITATION'):
            rest = text[len('ANSWER/CITATION'):].strip()
            if rest.startswith(':'):
                rest = rest[1:].strip()
            return f"Answer/Citation: {rest}"

        return text

    def _extract_citation(self, text: str) -> str:
        """Extract parenthetical citation from text."""
        # Find last parenthetical
        close = text.rfind(')')
        if close == -1:
            return ''

        open_paren = text.rfind('(', 0, close)
        if open_paren == -1:
            return ''

        return text[open_paren + 1:close].strip()

    def _find_page_reference(self, text: str) -> str:
        """Find page reference in text."""
        upper = text.upper()

        # Look for "Page X" or "P. X" patterns
        patterns = [
            (r'PAGE\s*[:\-]?\s*(\d+(?:\s*[-,]\s*\d+)*)', 1),
            (r'P\.\s*(\d+(?:\s*[-,]\s*\d+)*)', 1),
            (r'\(P\.?\s*(\d+(?:\s*[-,]\s*\d+)*)\)', 1),
        ]

        for pattern, group in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                page = match.group(group).strip()
                return f"Page {page}"

        return ''

    def _remove_citation_from_text(self, text: str) -> str:
        """Remove trailing parenthetical citation from text."""
        close = text.rfind(')')
        if close == -1:
            return text

        open_paren = text.rfind('(', 0, close)
        if open_paren == -1:
            return text

        return (text[:open_paren] + ' ' + text[close + 1:]).strip()
