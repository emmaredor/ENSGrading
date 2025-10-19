from http.server import BaseHTTPRequestHandler
import json
import yaml
import base64
import os
import sys
import tempfile
from datetime import datetime
from io import BytesIO

# Add the parent directory to the Python path to access existing modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from data_loader import DataLoader
    from text_formatter import TextFormatter
    from pdf_generator import TranscriptPDFGenerator
    from grades_processor import GradeValidator, RankingCalculator
except ImportError as e:
    # Fallback for Vercel deployment
    sys.path.append('/var/task')
    from data_loader import DataLoader
    from text_formatter import TextFormatter
    from pdf_generator import TranscriptPDFGenerator
    from grades_processor import GradeValidator, RankingCalculator


class TranscriptGenerator:
    """Main class for transcript generation operations."""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.text_formatter = TextFormatter()
        self.pdf_generator = TranscriptPDFGenerator()
        self.grade_validator = GradeValidator()
        self.ranking_calculator = RankingCalculator()

    def generate_single_transcript_from_data(self, student_info_data, author_info_data, grades_data, year_info_data=None, student_rankings=None):
        """
        Generate a single student transcript from raw data.
        
        Args:
            student_info_data: Dict containing student information
            author_info_data: Dict containing author information
            grades_data: List containing grades information
            year_info_data: Dict containing year information (optional)
            student_rankings: Dict containing student rankings (optional)
            
        Returns:
            Tuple of (pdf_content, filename, student_info)
        """
        print("=== SINGLE TRANSCRIPT GENERATION ===")
        
        # If year_info_data is not provided, create a default one
        if year_info_data is None:
            year_info_data = {'year': {
                'yearname': 'First year of Master\'s degree in Computer Science',
                'schoolyear': '2023-2024'
            }}
        
        # Combine the data properly using the text formatter
        student_data = self.text_formatter.combine_student_author_data(
            student_info_data, author_info_data, year_info_data
        )
        
        # Validate student data
        if not self.text_formatter.validate_required_fields(student_data):
            raise ValueError("Missing required fields in student data")
        
        # Load text templates
        text_templates_path = os.path.join(parent_dir, 'assets', 'text.json')
        print(f"Loading text templates from: {text_templates_path}")
        text_templates = self.data_loader.load_text_templates(text_templates_path)
        
        # Validate grades data using the validator
        print(f"Validating grades data...")
        is_valid, errors = self.grade_validator.validate_grades_data(grades_data)
        if not is_valid:
            raise ValueError(f"Invalid grades data: {'; '.join(errors)}")
        
        # Format text templates using the formatter
        print("Formatting text templates...")
        formatted_texts = self.text_formatter.format_all_templates(student_data, text_templates)
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{student_data['student']['firstname']}_{student_data['student']['name']}_transcript_{timestamp}.pdf"
        
        # Create temporary directory for PDF generation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate output path
            output_path = os.path.join(temp_dir, filename)
            print(f"Generating PDF: {output_path}")
            
            # Generate PDF using the PDF generator with optional rankings
            created_pdf = self.pdf_generator.generate_transcript(
                formatted_texts, student_data, grades_data, output_path, student_rankings
            )
            
            # Read the generated PDF
            with open(created_pdf, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
                
            print(f"\n✅ PDF GENERATED SUCCESSFULLY")
            print(f"📄 File: {filename}")
                
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
            print("DEBUG: Received POST request")
            # Read content length
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Get content type
            content_type = self.headers.get('Content-Type', '')
            print(f"DEBUG: Content-Type: {content_type}")
            
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
            
            print(f"DEBUG: Boundary extracted: {boundary}")
            
            # Parse multipart data
            form_data = self.parse_multipart(post_data, boundary)
            
            # Extract and parse files
            try:
                # Check for required files
                if b'student_info' not in form_data:
                    print("DEBUG: Missing student_info field")
                    self.send_error_response(400, 'Missing student_info file')
                    return
                    
                if b'author_info' not in form_data:
                    print("DEBUG: Missing author_info field")
                    self.send_error_response(400, 'Missing author_info file')
                    return
                    
                if b'grades' not in form_data:
                    print("DEBUG: Missing grades field")
                    self.send_error_response(400, 'Missing grades file')
                    return
                
                # Parse the files
                student_info_content = form_data[b'student_info'].decode('utf-8', errors='replace')
                author_info_content = form_data[b'author_info'].decode('utf-8', errors='replace')
                grades_content = form_data[b'grades'].decode('utf-8', errors='replace')
                
                print(f"DEBUG: Student info length: {len(student_info_content)}")
                print(f"DEBUG: Author info length: {len(author_info_content)}")
                print(f"DEBUG: Grades data length: {len(grades_content)}")
                
                student_info_data = yaml.safe_load(student_info_content)
                author_info_data = yaml.safe_load(author_info_content)
                grades_data = json.loads(grades_content)
                
                # Optional year info
                year_info_data = None
                if b'year_info' in form_data:
                    year_info_content = form_data[b'year_info'].decode('utf-8', errors='replace')
                    year_info_data = yaml.safe_load(year_info_content)
                    print("DEBUG: Year info parsed successfully")
                
                # Check for display rank flag
                display_rank = False
                if b'display_rank' in form_data:
                    rank_value = form_data[b'display_rank'].decode('utf-8').lower()
                    display_rank = rank_value in ('true', '1', 'yes', 'on')
                    print(f"DEBUG: Rank display setting: {display_rank}")
                
                print("DEBUG: All files parsed successfully")
                
            except Exception as e:
                print(f"DEBUG: Error parsing uploaded files: {str(e)}")
                self.send_error_response(400, f'Error parsing uploaded files: {str(e)}')
                return
            
            print("DEBUG: Starting transcript generation")
            # Generate transcript using the updated system
            generator = TranscriptGenerator()
            
            # Process with optional ranking if requested
            student_rankings = None
            if display_rank and b'rankings' in form_data:
                try:
                    rankings_content = form_data[b'rankings'].decode('utf-8', errors='replace')
                    student_rankings = json.loads(rankings_content)
                    print(f"DEBUG: Using provided rankings data")
                except Exception as e:
                    print(f"DEBUG: Error parsing rankings data: {str(e)}")
            
            pdf_content, filename, student_info = generator.generate_single_transcript_from_data(
                student_info_data, author_info_data, grades_data, year_info_data, student_rankings
            )
            
            # Encode PDF as base64
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            print(f"DEBUG: Generated PDF for {student_info['firstname']} {student_info['name']}")
            
            # Send success response
            self.send_success_response({
                'status': 'success',
                'message': 'Transcript generated successfully',
                'pdf_data': pdf_base64,
                'filename': filename,
                'student_name': f"{student_info['firstname']} {student_info['name']}"
            })
                
        except Exception as e:
            print(f"Error in single transcript generation: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_error_response(500, f'Server error: {str(e)}')
    
    def parse_multipart(self, data, boundary):
        """Parse multipart form data."""
        print(f"DEBUG: Parsing multipart data with boundary: {boundary}")
        form_data = {}
        boundary_delimiter = boundary.encode()
        parts = data.split(boundary_delimiter)
        print(f"DEBUG: Found {len(parts)} parts in multipart data")
        
        for i, part in enumerate(parts[1:-1]):  # Skip first empty part and last closing part
            print(f"DEBUG: Processing part {i+1}")
            if b'\r\n\r\n' in part:
                headers_section, content = part.split(b'\r\n\r\n', 1)
                headers = headers_section.decode('utf-8')
                print(f"DEBUG: Headers: {headers}")
                
                # Extract field name
                if 'name="' in headers:
                    field_name = headers.split('name="')[1].split('"')[0].encode('utf-8')
                    print(f"DEBUG: Field name: {field_name}")
                    
                    # Remove trailing boundary markers
                    content_start = content.find(b'\r\n')
                    if content_start != -1:
                        content = content[content_start + 2:].rstrip(b'\r\n--')
                    else:
                        content = content.rstrip(b'\r\n--')
                    
                    print(f"DEBUG: Content length for {field_name}: {len(content)} bytes")
                    form_data[field_name] = content
        
        print(f"DEBUG: Extracted fields: {list(form_data.keys())}")
        
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