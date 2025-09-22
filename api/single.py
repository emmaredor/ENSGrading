"""
Vercel Serverless Function for Single Student Transcript Generation
Uses the existing ENSGrading modules with proper architecture
"""

import json
import yaml
import base64
import os
import sys
import tempfile
from datetime import datetime

# Add the parent directory to the Python path to access existing modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

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


def parse_multipart_form_data(body, boundary):
    """Parse multipart form data from request body."""
    parts = {}
    
    # Simple multipart parsing (for demo purposes)
    # In production, you'd use a proper multipart parser
    try:
        sections = body.split(boundary.encode())
        for section in sections:
            if b'Content-Disposition' in section:
                # Extract field name
                if b'name="' in section:
                    name_start = section.find(b'name="') + 6
                    name_end = section.find(b'"', name_start)
                    field_name = section[name_start:name_end].decode()
                    
                    # Extract content (skip headers)
                    content_start = section.find(b'\r\n\r\n')
                    if content_start != -1:
                        content_start += 4
                        content = section[content_start:].rstrip(b'\r\n')
                        parts[field_name] = content
    except Exception:
        pass  # Fallback to empty parts
        
    return parts


def handler(request):
    """Vercel serverless function handler."""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
            },
            'body': ''
        }
    
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Parse multipart form data
        content_type = request.headers.get('content-type', '')
        if 'multipart/form-data' not in content_type:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Expected multipart/form-data'})
            }
        
        # Extract boundary
        boundary = None
        for part in content_type.split(';'):
            if 'boundary=' in part:
                boundary = '--' + part.split('boundary=')[1].strip()
                break
        
        if not boundary:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'No boundary found in multipart data'})
            }
        
        # Parse form data
        body = request.body if hasattr(request, 'body') else request.get('body', b'')
        if isinstance(body, str):
            body = body.encode()
            
        form_parts = parse_multipart_form_data(body, boundary)
        
        # Extract and parse files
        try:
            student_info_content = form_parts.get('student_info', b'').decode('utf-8')
            author_info_content = form_parts.get('author_info', b'').decode('utf-8')
            grades_content = form_parts.get('grades', b'').decode('utf-8')
            
            # Parse YAML and JSON
            student_info_data = yaml.safe_load(student_info_content) if student_info_content else None
            author_info_data = yaml.safe_load(author_info_content) if author_info_content else None
            grades_data = json.loads(grades_content) if grades_content else None
            
            if not all([student_info_data, author_info_data, grades_data]):
                raise ValueError("Missing required data: student_info, author_info, or grades")
                
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Error parsing uploaded files: {str(e)}'})
            }
        
        # Generate transcript using your existing system
        generator = TranscriptGenerator()
        pdf_content, filename, student_info = generator.generate_single_transcript_from_data(
            student_info_data, author_info_data, grades_data
        )
        
        # Encode PDF as base64
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept, Origin'
            },
            'body': json.dumps({
                'success': True,
                'pdf_data': pdf_base64,
                'filename': filename,
                'student_name': f"{student_info['firstname']} {student_info['name']}"
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }


# For Vercel
def lambda_handler(event, context):
    """AWS Lambda compatibility wrapper."""
    return handler(event)