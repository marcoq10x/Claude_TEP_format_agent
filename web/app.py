"""
Flask web server for the LLM Output Formatter dashboard.
"""

import os
import io
import tempfile
import zipfile
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
from src.csv_formatter import CSVFormatter
from src.rtf_formatter import RTFFormatter
from src.file_extractor import extract_text, is_supported

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
        'csv': (CSVFormatter(), 'text/csv'),
        'rtf': (RTFFormatter(), 'application/rtf'),
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


@app.route('/api/upload-format', methods=['POST'])
def upload_format():
    """
    Upload files, extract text server-side, format and return preview.

    Accepts multipart/form-data with 'files' and optional 'exam_type'.
    Supports: .txt, .docx, .pdf, .csv, .rtf
    """
    files = request.files.getlist('files')
    exam_type_str = request.form.get('exam_type', 'final')
    exam_type = ExamType.PRACTICE if exam_type_str == 'practice' else ExamType.FINAL

    if not files or len(files) == 0:
        return jsonify({'error': 'No files provided'}), 400

    if len(files) > 20:
        return jsonify({'error': 'Maximum 20 files allowed'}), 400

    results = []
    parser = ExamParser()

    for uploaded_file in files:
        filename = uploaded_file.filename or 'unknown.txt'

        if not is_supported(filename):
            results.append({
                'filename': filename,
                'success': False,
                'error': f'Unsupported file type: {Path(filename).suffix}'
            })
            continue

        try:
            # Save uploaded file to temp location
            with tempfile.NamedTemporaryFile(
                suffix=Path(filename).suffix,
                delete=False
            ) as tmp:
                uploaded_file.save(tmp.name)
                tmp_path = tmp.name

            # Extract text from the file
            content = extract_text(tmp_path, filename)

            # Clean up temp file
            os.unlink(tmp_path)

            # Parse the extracted text
            exam = parser.parse(content)

            result = {
                'filename': filename,
                'success': True,
                'stats': {
                    'question_count': len(exam.questions),
                    'answer_count': len(exam.answers)
                }
            }

            if not exam.is_balanced:
                result['warning'] = exam.mismatch_info

            results.append(result)

        except Exception as e:
            results.append({
                'filename': filename,
                'success': False,
                'error': str(e)
            })
            # Clean up temp file on error
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    return jsonify({
        'success': True,
        'results': results,
        'exam_type': exam_type.value
    })


@app.route('/api/upload-download/<format_type>', methods=['POST'])
def upload_download(format_type):
    """
    Upload files, extract text, format, and download as ZIP.

    format_type: 'docx', 'pdf', 'txt', 'csv', or 'rtf'
    Accepts multipart/form-data with 'files' and optional 'exam_type'.
    """
    files = request.files.getlist('files')
    exam_type_str = request.form.get('exam_type', 'final')
    exam_type = ExamType.PRACTICE if exam_type_str == 'practice' else ExamType.FINAL

    if not files or len(files) == 0:
        return jsonify({'error': 'No files provided'}), 400

    if len(files) > 20:
        return jsonify({'error': 'Maximum 20 files allowed'}), 400

    # Select formatter
    formatters = {
        'docx': (WordFormatter, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        'pdf': (PDFFormatter, 'application/pdf'),
        'txt': (TxtFormatter, 'text/plain'),
        'csv': (CSVFormatter, 'text/csv'),
        'rtf': (RTFFormatter, 'application/rtf'),
    }

    if format_type not in formatters:
        return jsonify({'error': f'Invalid format: {format_type}'}), 400

    FormatterClass, _ = formatters[format_type]

    try:
        parser = ExamParser()

        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for uploaded_file in files:
                filename = uploaded_file.filename or 'unknown.txt'

                if not is_supported(filename):
                    continue

                # Save uploaded file to temp location
                with tempfile.NamedTemporaryFile(
                    suffix=Path(filename).suffix,
                    delete=False
                ) as tmp:
                    uploaded_file.save(tmp.name)
                    input_tmp_path = tmp.name

                try:
                    # Extract text from the uploaded file
                    content = extract_text(input_tmp_path, filename)
                    os.unlink(input_tmp_path)

                    # Parse the extracted text
                    exam = parser.parse(content)

                    # Create formatter instance
                    formatter = FormatterClass()

                    # Generate output filename
                    base_name = Path(filename).stem
                    output_name = f"{base_name}_formatted{formatter.get_extension()}"

                    # Create temporary file for formatted output
                    with tempfile.NamedTemporaryFile(
                        suffix=formatter.get_extension(),
                        delete=False
                    ) as out_tmp:
                        output_path = Path(out_tmp.name)

                    formatter.format(exam, output_path, exam_type)

                    # Read formatted file and add to ZIP
                    with open(output_path, 'rb') as f:
                        zip_file.writestr(output_name, f.read())

                    # Clean up formatted temp file
                    if output_path.exists():
                        output_path.unlink()

                except Exception as e:
                    # Clean up on error
                    try:
                        os.unlink(input_tmp_path)
                    except Exception:
                        pass
                    raise e

        # Prepare ZIP for download
        zip_buffer.seek(0)

        type_label = 'practice' if exam_type == ExamType.PRACTICE else 'final'

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'formatted_{type_label}_exams.zip'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
