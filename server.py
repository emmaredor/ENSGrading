from flask import Flask, request, jsonify
import json
from api.single import TranscriptGenerator as SingleTranscriptGenerator
from api.batch import BatchTranscriptGenerator

app = Flask(__name__)

# Initialize generators
single_generator = SingleTranscriptGenerator()
batch_generator = BatchTranscriptGenerator()

@app.route('/')
def home():
    return "Welcome to the ENS Grading API!"

@app.route('/api/single', methods=['POST'])
def generate_single():
    try:
        # Extract JSON data from the request
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Extract required fields
        student_info = data.get("student_info")
        author_info = data.get("author_info")
        grades = data.get("grades")

        if not (student_info and author_info and grades):
            return jsonify({"error": "Missing required fields"}), 400

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

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch', methods=['POST'])
def generate_batch():
    try:
        # Extract files and author info from the request
        excel_file = request.files.get("students_excel")
        author_info = request.form.get("author_info")

        if not (excel_file and author_info):
            return jsonify({"error": "Missing required fields"}), 400

        # Read the Excel file and author info
        excel_data = excel_file.read()
        author_info_data = json.loads(author_info)

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

if __name__ == '__main__':
    app.run(debug=True)