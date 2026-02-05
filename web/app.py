"""
Flask web server for the LLM Output Formatter dashboard.
"""

import os
import io
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import ExamParser
from src.formatter import ExamType
from src.word_formatter import WordFormatter
from src.pdf_formatter import PDFFormatter
from src.txt_formatter import TxtFormatter

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')


def _get_exam_type(data: dict) -> ExamType:
    """Extract exam type from request data, defaulting to FINAL."""
    exam_type_str = data.get('exam_type', 'final')
    if exam_type_str == 'practice':
        return ExamType.PRACTICE
    return ExamType.FINAL


@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html')


@app.route('/api/format', methods=['POST'])
def format_text():
    """
    Format the input text and return formatted output.

    Expects JSON with 'text' and optional 'exam_type' field.
    Returns JSON with 'questions' and 'answers' fields.
    """
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    input_text = data['text']
    exam_type = _get_exam_type(data)

    try:
        parser = ExamParser()
        exam = parser.parse(input_text)

        # Format questions for display
        formatted_questions = []
        for q in exam.questions:
            q_data = {
                'number': q.number,
                'text': q.text,
                'choices': [
                    {'letter': c.letter, 'text': c.text}
                    for c in q.choices
                ]
            }
            formatted_questions.append(q_data)

        # Format answers for display
        formatted_answers = []
        for a in exam.answers:
            a_data = {
                'number': a.question_number,
                'letter': a.answer_letter,
                'payload': a.payload
            }
            formatted_answers.append(a_data)

        response = {
            'success': True,
            'title': exam.title or 'Exam',
            'questions': formatted_questions,
            'answers': formatted_answers,
            'exam_type': exam_type.value,
            'stats': {
                'question_count': len(exam.questions),
                'answer_count': len(exam.answers)
            }
        }

        # Add warning if question/answer counts don't match
        if not exam.is_balanced:
            response['warning'] = exam.mismatch_info

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<format_type>', methods=['POST'])
def download_file(format_type):
    """
    Generate and download formatted file.

    format_type: 'docx', 'pdf', or 'txt'
    Expects JSON with 'text' and optional 'exam_type' field.
    """
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    input_text = data['text']
    exam_type = _get_exam_type(data)

    # Select formatter
    formatters = {
        'docx': (WordFormatter(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        'pdf': (PDFFormatter(), 'application/pdf'),
        'txt': (TxtFormatter(), 'text/plain'),
    }

    if format_type not in formatters:
        return jsonify({'error': f'Invalid format: {format_type}'}), 400

    formatter, mimetype = formatters[format_type]

    try:
        parser = ExamParser()
        exam = parser.parse(input_text)

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            suffix=formatter.get_extension(),
            delete=False
        ) as tmp:
            output_path = Path(tmp.name)

        formatter.format(exam, output_path, exam_type)

        # Build download filename
        type_label = 'practice' if exam_type == ExamType.PRACTICE else 'final'

        # Read file and send
        return send_file(
            output_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=f'formatted_{type_label}_exam{formatter.get_extension()}'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
