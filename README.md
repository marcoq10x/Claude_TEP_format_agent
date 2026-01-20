# LLM Output Formatter

AI Agent that formats exam content from LLM outputs into properly formatted MS Word (.docx), PDF, or plain text (.txt) files.

## Features

- **Multiple Output Formats**: Export to Word, PDF, or TXT
- **Intelligent Parsing**: Automatically detects questions, choices, and answer keys
- **Proper Formatting**:
  - Times New Roman, 12pt font
  - 0.5 inch margins
  - Proper indentation for multiple choice options
  - Answer key starts on a new page
  - Questions and choices kept together (not split across pages)
- **Flexible Input**: Handles various LLM output formats with Q1, 1., etc. numbering

## Installation

```bash
# Clone the repository
git clone https://github.com/marcoq10x/Claude_TEP_format_agent.git
cd Claude_TEP_format_agent

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
# Convert to Word document
python -m src.main input.txt -o output.docx

# Convert to PDF
python -m src.main input.txt -o output.pdf

# Convert to plain text
python -m src.main input.txt -o output.txt

# Read from stdin
echo "Q1. Question? A. a B. b C. c D. d" | python -m src.main - -o output.docx
```

### Python API

```python
from src.main import format_text

# Format text to Word document
format_text(exam_text, "output.docx")

# Format to PDF
format_text(exam_text, "output.pdf", output_format="pdf")

# Format to TXT
format_text(exam_text, "output.txt", output_format="txt")
```

## Input Format

The parser accepts various input formats:

### Questions
```
Q1. What is the capital of France?
A. London
B. Paris
C. Berlin
D. Rome

Q2. What is 2+2? A. 3 B. 4 C. 5 D. 6
```

### Answer Key
```
Answer Key

Q1 "B" Paris is the capital (Page 45)
Q2 "B" Basic arithmetic (Page 12)
```

Or with Answer/Citation format:
```
Q1 B) Answer/Citation: Page 45
```

## Output Format

### Word/PDF Output
- **Questions**: `1.    <question text>` (with blank line after)
- **Choices**: Indented 0.25 inches as `A.    <choice text>`
- **Answer Key**: Starts on new page, formatted as `1.    B)    <explanation> Answer/Citation: Page X`

### Text Output
- Same formatting with ASCII separators for sections

## Project Structure

```
Claude_TEP_format_agent/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI and API entry point
│   ├── parser.py            # Text parsing logic
│   ├── formatter.py         # Base formatter class
│   ├── word_formatter.py    # MS Word output
│   ├── pdf_formatter.py     # PDF output
│   └── txt_formatter.py     # Plain text output
├── tests/
│   └── test_parser.py       # Parser unit tests
├── samples/
│   └── sample_exam.txt      # Example input file
├── requirements.txt
└── README.md
```

## Dependencies

- `python-docx` - Word document generation
- `reportlab` - PDF generation
- `click` - CLI interface

## Testing

```bash
pip install pytest
python -m pytest tests/ -v
```

## License

MIT License
