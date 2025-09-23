from http.server import BaseHTTPRequestHandler
import json
import yaml
import base64
import os
import sys
import tempfile
from datetime import datetime

# Add the parent directory to the Python path to access existing modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from data_loader import DataLoader
    from text_formatter import TextFormatter
    from pdf_generator import TranscriptPDFGenerator
    from grades_processor import GradeValidator
except ImportError as e:
    # Fallback for Vercel deployment
    sys.path.append('/var/task')
    from data_loader import DataLoader
    from text_formatter import TextFormatter
    from pdf_generator import TranscriptPDFGenerator
    from grades_processor import GradeValidator


class TranscriptGenerator:
    """Main class for transcript generation operations."""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.text_formatter = TextFormatter()
        self.pdf_generator = TranscriptPDFGenerator()
        self.grade_validator = GradeValidator()

    def generate_single_transcript_from_data(self, student_info_data, author_info_data, grades_data):
        """
        Generate a single student transcript from raw data.
        
        Args:
            student_info_data: Dict containing student information
            author_info_data: Dict containing author information
            grades_data: List containing grades information
            
        Returns:
            Tuple of (pdf_content, filename, student_info)
        """
        
        # Combine the data properly using your text formatter
        student_data = self.text_formatter.combine_student_author_data(
            student_info_data, author_info_data
        )
        
        # Validate student data
        if not self.text_formatter.validate_required_fields(student_data):
            raise ValueError("Missing required fields in student data")
        
        # Load text templates
        text_templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'text.json')
        text_templates = self.data_loader.load_text_templates(text_templates_path)
        
        # Validate grades data using your validator
        is_valid, errors = self.grade_validator.validate_grades_data(grades_data)
        if not is_valid:
            raise ValueError(f"Invalid grades data: {'; '.join(errors)}")
        
        # Format text templates using your formatter
        formatted_texts = self.text_formatter.format_all_templates(student_data, text_templates)
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{student_data['student']['firstname']}_{student_data['student']['name']}_transcript_{timestamp}.pdf"
        
        # Create temporary directory for PDF generation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate output path
            output_path = os.path.join(temp_dir, filename)
            
            # Generate PDF using your PDF generator
            created_pdf = self.pdf_generator.generate_transcript(
                formatted_texts, student_data, grades_data, output_path
            )
            
            # Read the generated PDF
            with open(created_pdf, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
                
            return pdf_content, filename, student_data['student']


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
                student_info_data = yaml.safe_load(form_data.get('student_info', b'').decode('utf-8', errors='replace'))
                author_info_data = yaml.safe_load(form_data.get('author_info', b'').decode('utf-8', errors='replace'))
                grades_data = json.loads(form_data.get('grades', b'').decode('utf-8', errors='replace'))
                
                if not all([student_info_data, author_info_data, grades_data]):
                    raise ValueError("Missing required data: student_info, author_info, or grades")
                    
            except Exception as e:
                self.send_error_response(400, f'Error parsing uploaded files: {str(e)}')
                return
            
            # Generate transcript using your existing system
            generator = TranscriptGenerator()
            pdf_content, filename, student_info = generator.generate_single_transcript_from_data(
                student_info_data, author_info_data, grades_data
            )
            
            # Encode PDF as base64
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # Send success response
            self.send_success_response({
                'success': True,
                'pdf_data': pdf_base64,
                'filename': filename,
                'student_name': f"{student_info['firstname']} {student_info['name']}"
            })
                
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