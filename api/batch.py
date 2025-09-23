from http.server import BaseHTTPRequestHandler
import json
import yaml
import base64
import os
import sys
import tempfile
import zipfile
from datetime import datetime
from io import BytesIO

# Add the parent directory to the Python path to access existing modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from data_loader import DataLoader, ExcelStudentLoader
    from text_formatter import TextFormatter
    from pdf_generator import TranscriptPDFGenerator
    from grades_processor import GradeValidator
except ImportError as e:
    # Fallback for Vercel deployment
    sys.path.append('/var/task')
    from data_loader import DataLoader, ExcelStudentLoader
    from text_formatter import TextFormatter
    from pdf_generator import TranscriptPDFGenerator
    from grades_processor import GradeValidator


class BatchTranscriptGenerator:
    """Main class for batch transcript generation operations."""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.excel_loader = ExcelStudentLoader()
        self.text_formatter = TextFormatter()
        self.pdf_generator = TranscriptPDFGenerator()
        self.grade_validator = GradeValidator()

    def generate_batch_transcripts_from_data(self, excel_data, author_info_data):
        """
        Generate multiple student transcripts from Excel data.
        
        Args:
            excel_data: Bytes content of Excel file
            author_info_data: Dict containing author information
            
        Returns:
            Tuple of (zip_content, zip_filename, student_names, generated_count)
        """
        print("=== BATCH TRANSCRIPT GENERATION ===")
        
        # Create temporary files for Excel processing
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as excel_temp:
            excel_temp.write(excel_data)
            excel_temp_path = excel_temp.name
        
        try:
            # Load students from Excel
            students = self.excel_loader.load_students_from_excel(excel_temp_path)
            print(f"✅ Loaded {len(students)} students from Excel")
            
            # Load text templates
            text_templates = self.data_loader.load_text_templates(
                os.path.join(parent_dir, 'assets/text.json')
            )
            
            generated_pdfs = []
            student_names = []
            successful_count = 0
            
            # Create in-memory ZIP file
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, student_excel_data in enumerate(students):
                    try:
                        print(f"\n--- Processing student {i+1}/{len(students)} ---")
                        
                        # Skip students with no grades
                        if not student_excel_data['grades']:
                            print(f"⚠️  Skipping student {i+1}: No grades found")
                            continue
                        
                        # Combine student data with author data
                        student_data = self.text_formatter.combine_student_author_data(
                            {'student': student_excel_data['student']}, {'author': author_info_data}
                        )
                        
                        student_name = f"{student_data['student']['firstname']} {student_data['student']['name']}"
                        print(f"👤 Student: {student_name}")
                        print(f"📚 Courses: {len(student_excel_data['grades'])}")
                        
                        # Validate grades data
                        is_valid, errors = self.grade_validator.validate_grades_data(student_excel_data['grades'])
                        if not is_valid:
                            print(f"❌ Invalid grades data for student {i+1}: {'; '.join(errors)}")
                            continue
                        
                        # Format text templates
                        formatted_texts = self.text_formatter.format_all_templates(student_data, text_templates)
                        
                        # Create grades for PDF generation
                        grades_for_pdf = student_excel_data['grades']
                        
                        # Generate PDF filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        pdf_filename = f"{student_data['student']['firstname']}_{student_data['student']['name']}_transcript_{timestamp}_{i+1:03d}.pdf"
                        
                        # Create temporary file for PDF generation
                        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_temp:
                            pdf_temp_path = pdf_temp.name
                        
                        try:
                            # Generate PDF using the correct method
                            created_pdf = self.pdf_generator.generate_transcript(
                                formatted_texts, student_data, grades_for_pdf, pdf_temp_path
                            )
                            
                            # Read the generated PDF
                            with open(created_pdf, 'rb') as pdf_file:
                                pdf_content = pdf_file.read()
                            
                            # Add PDF to ZIP
                            zip_file.writestr(pdf_filename, pdf_content)
                            
                        finally:
                            # Clean up temporary PDF file
                            if os.path.exists(pdf_temp_path):
                                os.unlink(pdf_temp_path)
                        
                        student_names.append(student_name)
                        successful_count += 1
                        
                        print(f"✅ Generated PDF for {student_name}")
                        
                    except Exception as e:
                        print(f"❌ Error processing student {i+1}: {str(e)}")
                        continue
            
            # Get ZIP content
            zip_buffer.seek(0)
            zip_content = zip_buffer.getvalue()
            
            # Generate ZIP filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"batch_transcripts_{timestamp}.zip"
            
            print(f"\n✅ BATCH GENERATION COMPLETED")
            print(f"📄 Generated {successful_count} transcripts")
            print(f"📦 ZIP file: {zip_filename}")
            
            return zip_content, zip_filename
            
        finally:
            # Clean up temporary file
            if os.path.exists(excel_temp_path):
                os.unlink(excel_temp_path)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
        self.end_headers()

    def do_POST(self):
        """Handle POST requests for batch transcript generation."""
        try:
            print("DEBUG: Received POST request")
            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            print(f"DEBUG: Content-Type: {content_type}")
            if not content_type.startswith('multipart/form-data'):
                self.send_error_response(400, 'Content-Type must be multipart/form-data')
                return

            # Extract boundary
            boundary = None
            for part in content_type.split(';'):
                if 'boundary=' in part:
                    boundary = part.split('boundary=')[1].strip()
                    break
            
            if not boundary:
                self.send_error_response(400, 'No boundary found in Content-Type')
                return

            print(f"DEBUG: Boundary extracted: {boundary}")

            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            print(f"DEBUG: Content-Length: {content_length}")
            if content_length == 0:
                self.send_error_response(400, 'No data received')
                return

            body = self.rfile.read(content_length)
            print(f"DEBUG: Read {len(body)} bytes from request body")
            
            # Parse form data
            form_data = self.parse_multipart_form_data(body, boundary.encode())
            
            # Validate required fields
            if b'students_excel' not in form_data:
                print("DEBUG: Missing students_excel field")
                self.send_error_response(400, 'Missing students_excel file')
                return
                
            if b'author_info' not in form_data:
                print("DEBUG: Missing author_info field")
                self.send_error_response(400, 'Missing author_info file')
                return

            print("DEBUG: Both required fields found")

            # Parse author info YAML
            try:
                author_yaml_content = form_data[b'author_info'].decode('utf-8')
                print(f"DEBUG: Author YAML content length: {len(author_yaml_content)}")
                print(f"DEBUG: Author YAML preview: {author_yaml_content[:100]}...")
                author_data = yaml.safe_load(author_yaml_content)
                if 'author' not in author_data:
                    raise ValueError("YAML must contain 'author' key")
                author_info = author_data['author']
                print("DEBUG: Author info parsed successfully")
            except Exception as e:
                print(f"DEBUG: Error parsing author YAML: {str(e)}")
                self.send_error_response(400, f'Invalid author info YAML: {str(e)}')
                return

            print("DEBUG: Starting batch generation")
            # Generate batch transcripts
            generator = BatchTranscriptGenerator()
            
            excel_data = form_data[b'students_excel']
            print(f"DEBUG: Excel data size: {len(excel_data)} bytes")
            zip_content, zip_filename, student_names, generated_count = generator.generate_batch_transcripts_from_data(
                excel_data, author_info
            )
            
            # Encode ZIP content as base64
            zip_base64 = base64.b64encode(zip_content).decode('utf-8')
            print(f"DEBUG: Generated ZIP with {generated_count} transcripts")
            
            # Return success response
            response_data = {
                'status': 'success',
                'message': 'Batch transcripts generated successfully',
                'zip_data': zip_base64,
                'filename': zip_filename,
                'student_names': student_names,
                'generated_count': generated_count
            }
            
            self.send_success_response(response_data)
            
        except Exception as e:
            print(f"Error in batch transcript generation: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_error_response(500, f'Internal server error: {str(e)}')

    def parse_multipart_form_data(self, body, boundary):
        """Parse multipart/form-data from request body."""
        print(f"DEBUG: Parsing multipart data with boundary: {boundary}")
        form_data = {}
        boundary_delimiter = b'--' + boundary
        parts = body.split(boundary_delimiter)
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