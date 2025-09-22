from http.server import BaseHTTPRequestHandler
import json
import yaml
import base64
import os
import sys
import tempfile
from datetime import datetime
import urllib.parse

# Add the parent directory to the Python path to access existing modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_loader import DataLoader
from text_formatter import TextFormatter
from pdf_generator import TranscriptPDFGenerator
from grades_processor import GradeValidator


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
        self.end_headers()
        
    def do_POST(self):
        try:
            # Read content length
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Get content type
            content_type = self.headers.get('Content-Type', '')
            
            if 'multipart/form-data' not in content_type:
                self.send_error_response(400, 'Expected multipart/form-data')
                return
            
            # Extract boundary
            boundary = None
            for part in content_type.split(';'):
                if 'boundary=' in part:
                    boundary = '--' + part.split('boundary=')[1].strip()
                    break
            
            if not boundary:
                self.send_error_response(400, 'No boundary found')
                return
            
            # Parse multipart data
            form_data = self.parse_multipart(post_data, boundary)
            
            # Extract and parse files
            try:
                student_info_data = yaml.safe_load(form_data.get('student_info', b'').decode('utf-8'))
                author_info_data = yaml.safe_load(form_data.get('author_info', b'').decode('utf-8'))
                grades_data = json.loads(form_data.get('grades', b'').decode('utf-8'))
                
                if not all([student_info_data, author_info_data, grades_data]):
                    raise ValueError("Missing required data")
                    
            except Exception as e:
                self.send_error_response(400, f'Error parsing files: {str(e)}')
                return
            
            # Generate transcript
            try:
                # Load and validate data
                text_formatter = TextFormatter()
                grade_validator = GradeValidator()
                
                # Validate grades
                validated_grades = grade_validator.validate_grades(grades_data)
                
                # Format text data
                formatted_student = text_formatter.format_student_info(student_info_data)
                formatted_author = text_formatter.format_author_info(author_info_data)
                formatted_grades = text_formatter.format_grades_info(validated_grades)
                
                # Generate PDF
                pdf_generator = TranscriptPDFGenerator()
                pdf_content = pdf_generator.generate_pdf(
                    formatted_student, 
                    formatted_author, 
                    formatted_grades
                )
                
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{formatted_student['firstname']}_{formatted_student['name']}_transcript_{timestamp}.pdf"
                
                # Encode PDF as base64
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                
                # Send success response
                self.send_success_response({
                    'success': True,
                    'pdf_data': pdf_base64,
                    'filename': filename,
                    'student_name': f"{formatted_student['firstname']} {formatted_student['name']}"
                })
                
            except Exception as e:
                self.send_error_response(500, f'PDF generation failed: {str(e)}')
                
        except Exception as e:
            self.send_error_response(500, f'Server error: {str(e)}')
    
    def parse_multipart(self, data, boundary):
        """Parse multipart form data."""
        form_data = {}
        parts = data.split(boundary.encode())
        
        for part in parts:
            if b'Content-Disposition' in part:
                # Extract field name
                lines = part.split(b'\r\n')
                for line in lines:
                    if b'Content-Disposition' in line:
                        disp_line = line.decode()
                        if 'name="' in disp_line:
                            field_name = disp_line.split('name="')[1].split('"')[0]
                            # Extract content (skip headers)
                            content_start = part.find(b'\r\n\r\n')
                            if content_start != -1:
                                content = part[content_start + 4:].rstrip(b'\r\n--')
                                form_data[field_name] = content
                            break
        
        return form_data
    
    def send_success_response(self, data):
        """Send a successful JSON response with CORS headers."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_error_response(self, status_code, message):
        """Send an error JSON response with CORS headers."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode())