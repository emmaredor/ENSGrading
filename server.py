from flask import Flask, request, jsonify
import json
from api.single import TranscriptGenerator as SingleTranscriptGenerator
from api.batch import BatchTranscriptGenerator
from flask_cors import CORS
import yaml

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
            student_info = request.files.get('student_info')
            author_info = request.files.get('author_info')
            grades = request.files.get('grades')

            if not (student_info and author_info and grades):
                return jsonify({"error": "Missing required fields"}), 400

            # Parse the uploaded files
            student_data = yaml.safe_load(student_info.stream.read().decode('utf-8', errors='ignore'))
            author_data = yaml.safe_load(author_info.stream.read().decode('utf-8', errors='ignore'))
            grades_data = json.loads(grades.stream.read().decode('utf-8', errors='ignore'))

            # Generate the transcript
            pdf_content, filename, student_info = single_generator.generate_single_transcript_from_data(
                student_data, author_data, grades_data
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

        # Read the Excel file and author YAML file
        excel_data = excel_file.read()
        author_info_data = yaml.safe_load(author_info_file.stream.read().decode('utf-8', errors='ignore'))

        # Generate the transcripts
        zip_content, zip_filename, student_names, generated_count = batch_generator.generate_batch_transcripts_from_data(
            excel_data, author_info_data
        )

        # Return the ZIP content as a base64 string
        return jsonify({
            "zip_filename": zip_filename,
            "zip_content": zip_content.decode('utf-8'),
            "student_names": student_names,
            "generated_count": generated_count
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500