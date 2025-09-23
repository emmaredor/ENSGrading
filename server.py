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

            # Create temporary files to use with the data loader
            import tempfile
            import os
            
            # For student info
            with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as temp_student:
                temp_student.write(student_info_file.read())
                student_info_path = temp_student.name
            
            # For author info
            with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as temp_author:
                temp_author.write(author_info_file.read())
                author_info_path = temp_author.name
            
            # For grades
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_grades:
                temp_grades.write(grades_file.read())
                grades_path = temp_grades.name
            
            try:
                # Use the DataLoader to load files (same way as in main.py)
                from data_loader import DataLoader
                data_loader = DataLoader()
                
                student_info = data_loader.load_student_info(student_info_path)
                author_info = data_loader.load_author_info(author_info_path)
                grades = data_loader.load_grades_data(grades_path)
            finally:
                # Clean up temporary files
                for path in [student_info_path, author_info_path, grades_path]:
                    if os.path.exists(path):
                        os.remove(path)

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
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error in generate_single: {str(e)}")
        print(error_detail)
        return jsonify({"error": str(e), "detail": error_detail}), 500

@app.route('/api/batch', methods=['POST'])
def generate_batch():
    try:
        # Extract files from the request
        excel_file = request.files.get("students_excel")
        author_info_file = request.files.get("author_info")

        if not (excel_file and author_info_file):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Create temporary files for processing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_excel:
            temp_excel.write(excel_file.read())
            excel_path = temp_excel.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as temp_author:
            temp_author.write(author_info_file.read())
            author_path = temp_author.name
        
        try:
            # Use the data loader to read the author info properly
            from data_loader import DataLoader
            data_loader = DataLoader()
            author_info = data_loader.load_author_info(author_path)
            
            # Generate the transcripts
            zip_content, zip_filename = batch_generator.generate_batch_transcripts_from_data(
                excel_file, author_info_file
            )
        finally:
            # Clean up temporary files
            for path in [excel_path, author_path]:
                if os.path.exists(path):
                    os.remove(path)

        # Return the ZIP file as a downloadable response
        return send_file(BytesIO(zip_content), mimetype='application/zip', as_attachment=True, download_name=zip_filename)

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error in generate_batch: {str(e)}")
        print(error_detail)
        return jsonify({"error": str(e), "detail": error_detail}), 500