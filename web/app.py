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
from src.word_formatter import WordFormatter
from src.pdf_formatter import PDFFormatter
from src.txt_formatter import TxtFormatter

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')


@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html')


@app.route('/api/format', methods=['POST'])
def format_text():
    """
    Format the input text and return formatted output.

    Expects JSON with 'text' field.
    Returns JSON with 'questions' and 'answers' fields.
    """
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    input_text = data['text']

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

        return jsonify({
            'success': True,
            'questions': formatted_questions,
            'answers': formatted_answers,
            'stats': {
                'question_count': len(exam.questions),
                'answer_count': len(exam.answers)
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<format_type>', methods=['POST'])
def download_file(format_type):
    """
    Generate and download formatted file.

    format_type: 'docx', 'pdf', or 'txt'
    """
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    input_text = data['text']

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

        formatter.format(exam, output_path)

        # Read file and send
        return send_file(
            output_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=f'formatted_exam{formatter.get_extension()}'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
