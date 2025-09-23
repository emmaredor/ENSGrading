from flask import Flask, request, jsonify, send_file
import json
from api.single import TranscriptGenerator as SingleTranscriptGenerator
from api.batch import BatchTranscriptGenerator
from flask_cors import CORS
import yaml
from io import BytesIO

app = Flask(__name__)

# Enable CORS for the Flask app
CORS(app)

# Initialize generators
single_generator = SingleTranscriptGenerator()
batch_generator = BatchTranscriptGenerator()

@app.route('/')
def home():
    return "Welcome to the ENS Grading API!"

@app.route('/api/single', methods=['POST'])
def generate_single():
    try:
        # Check if the request is multipart/form-data
        if request.content_type.startswith('multipart/form-data'):
            student_info_file = request.files.get('student_info')
            author_info_file = request.files.get('author_info')
            grades_file = request.files.get('grades')

            if not (student_info_file and author_info_file and grades_file):
                return jsonify({"error": "Missing required fields"}), 400

            # Parse the file contents into Python data structures
            student_info = yaml.safe_load(student_info_file.read().decode('utf-8'))
            author_info = yaml.safe_load(author_info_file.read().decode('utf-8'))
            grades = json.loads(grades_file.read().decode('utf-8'))

            # Generate the transcript
            pdf_content, filename, student_info = single_generator.generate_single_transcript_from_data(
                student_info, author_info, grades
            )

            # Return the PDF content as a base64 string
            return jsonify({
                "filename": filename,
                "pdf_content": pdf_content.decode('utf-8'),
                "student_info": student_info
            }), 200

        return jsonify({"error": "Unsupported Media Type: Content-Type must be multipart/form-data"}), 415

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch', methods=['POST'])
def generate_batch():
    try:
        # Extract files from the request
        excel_file = request.files.get("students_excel")
        author_info_file = request.files.get("author_info")

        if not (excel_file and author_info_file):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Generate the transcripts
        zip_content, zip_filename = batch_generator.generate_batch_transcripts_from_data(
            excel_file, author_info_file
        )

        # Return the ZIP file as a downloadable response
        return send_file(BytesIO(zip_content), mimetype='application/zip', as_attachment=True, download_name=zip_filename)

    except Exception as e:
        return jsonify({"error": str(e)}), 500