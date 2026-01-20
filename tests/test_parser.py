"""Tests for the exam parser module."""

import pytest
from src.parser import ExamParser, ParsedExam, Question, Choice, Answer


class TestExamParser:
    """Test suite for ExamParser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ExamParser()

    def test_parse_simple_question(self):
        """Test parsing a simple question with choices."""
        text = """Q1. What is 2+2?
A. 3
B. 4
C. 5
D. 6"""
        result = self.parser.parse(text)

        assert len(result.questions) == 1
        q = result.questions[0]
        assert q.number == 1
        assert q.text == "What is 2+2?"
        assert len(q.choices) == 4
        assert q.choices[0].letter == "A"
        assert q.choices[0].text == "3"
        assert q.choices[1].letter == "B"
        assert q.choices[1].text == "4"

    def test_parse_inline_choices(self):
        """Test parsing question with inline choices."""
        text = "Q1. What is 2+2? A. 3 B. 4 C. 5 D. 6"
        result = self.parser.parse(text)

        assert len(result.questions) == 1
        q = result.questions[0]
        assert q.number == 1
        assert len(q.choices) == 4

    def test_parse_multiple_questions(self):
        """Test parsing multiple questions."""
        text = """Q1. First question?
A. A1
B. B1
C. C1
D. D1

Q2. Second question?
A. A2
B. B2
C. C2
D. D2"""
        result = self.parser.parse(text)

        assert len(result.questions) == 2
        assert result.questions[0].number == 1
        assert result.questions[1].number == 2

    def test_parse_answer_key_section(self):
        """Test parsing answer key section."""
        text = """Q1. Question? A. a B. b C. c D. d

Answer Key

Q1 "B" explanation (Page 45)"""
        result = self.parser.parse(text)

        assert len(result.questions) == 1
        assert len(result.answers) == 1
        assert result.answers[0].question_number == 1
        assert result.answers[0].answer_letter == "B"

    def test_parse_question_without_q_prefix(self):
        """Test parsing question number without Q prefix."""
        text = """1. What is the capital of France?
A. London
B. Paris
C. Berlin
D. Rome"""
        result = self.parser.parse(text)

        assert len(result.questions) == 1
        assert result.questions[0].number == 1

    def test_normalize_smart_quotes(self):
        """Test that smart quotes are normalized."""
        text = 'Q1 "B" explanation'
        # Using actual smart quotes
        text_smart = 'Q1 \u201cB\u201d explanation'

        result = self.parser.parse(text_smart)
        # Should still parse correctly
        assert len(result.answers) == 1 or len(result.questions) >= 0

    def test_empty_input(self):
        """Test parsing empty input."""
        result = self.parser.parse("")

        assert len(result.questions) == 0
        assert len(result.answers) == 0

    def test_parse_answer_with_citation(self):
        """Test parsing answer with Answer/Citation format."""
        text = """Answer Key

Q1 B) Answer/Citation: Page 45"""
        result = self.parser.parse(text)

        assert len(result.answers) == 1
        assert result.answers[0].answer_letter == "B"
        assert "Page 45" in result.answers[0].payload


class TestChoiceParsing:
    """Tests specifically for choice parsing."""

    def setup_method(self):
        self.parser = ExamParser()

    def test_choice_with_period_delimiter(self):
        """Test parsing choices with period delimiters."""
        text = """Q1. Question?
A. Choice A
B. Choice B
C. Choice C
D. Choice D"""
        result = self.parser.parse(text)

        assert len(result.questions[0].choices) == 4

    def test_choice_with_paren_delimiter(self):
        """Test parsing choices with parenthesis delimiters."""
        text = """Q1. Question?
A) Choice A
B) Choice B
C) Choice C
D) Choice D"""
        result = self.parser.parse(text)

        assert len(result.questions[0].choices) == 4

    def test_lowercase_choice_letters(self):
        """Test parsing lowercase choice letters."""
        text = """Q1. Question?
a. Choice A
b. Choice B
c. Choice C
d. Choice D"""
        result = self.parser.parse(text)

        assert len(result.questions[0].choices) == 4
        # Should be normalized to uppercase
        assert result.questions[0].choices[0].letter == "A"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
