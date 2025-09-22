"""
Vercel Serverless Function for Batch Student Transcript Generation
Uses the existing ENSGrading modules with proper architecture
"""

import json
import yaml
import base64
import os
import sys
import tempfile
import zipfile
from datetime import datetime

# Add the parent directory to the Python path to access existing modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data_loader import DataLoader, ExcelStudentLoader
from text_formatter import TextFormatter
from pdf_generator import TranscriptPDFGenerator
from grades_processor import GradeValidator


class BatchTranscriptGenerator:
    """Batch transcript generation using existing ENS modules."""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.excel_loader = ExcelStudentLoader()
        self.text_formatter = TextFormatter()
        self.pdf_generator = TranscriptPDFGenerator()
        self.grade_validator = GradeValidator()

    def generate_batch_transcripts_from_excel(self, excel_content, author_info_data):
        """
        Generate multiple transcripts from Excel data.
        
        Args:
            excel_content: Raw Excel file content
            author_info_data: Dict containing author information
            
        Returns:
            Tuple of (zip_content, zip_filename, generated_count)
        """
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save Excel file temporarily
            excel_path = os.path.join(temp_dir, 'students.xlsx')
            with open(excel_path, 'wb') as f:
                f.write(excel_content)
            
            # Load text templates
            text_templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'text.json')
            text_templates = self.data_loader.load_text_templates(text_templates_path)
            
            # Load students from Excel using your existing loader
            students = self.excel_loader.load_students_from_excel(excel_path)
            
            # Create ZIP file for all transcripts
            zip_path = os.path.join(temp_dir, 'batch_transcripts.zip')
            generated_count = 0
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, student_excel_data in enumerate(students):
                    try:
                        # Skip students with no grades
                        if not student_excel_data['grades']:
                            continue
                        
                        # Combine student data with author data using your formatter
                        student_data = self.text_formatter.combine_student_author_data(
                            {'student': student_excel_data['student']}, author_info_data
                        )
                        
                        # Validate grades data using your validator
                        is_valid, errors = self.grade_validator.validate_grades_data(student_excel_data['grades'])
                        if not is_valid:
                            continue
                        
                        # Format text templates using your formatter
                        formatted_texts = self.text_formatter.format_all_templates(student_data, text_templates)
                        
                        # Generate PDF filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        pdf_filename = f"{student_data['student']['firstname']}_{student_data['student']['name']}_transcript_{timestamp}_{i+1:03d}.pdf"
                        pdf_path = os.path.join(temp_dir, pdf_filename)
                        
                        # Generate PDF using your PDF generator
                        created_pdf = self.pdf_generator.generate_transcript(
                            formatted_texts, student_data, student_excel_data['grades'], pdf_path
                        )
                        
                        # Add PDF to ZIP
                        zip_file.write(created_pdf, pdf_filename)
                        generated_count += 1
                        
                    except Exception as e:
                        # Skip this student if there's an error
                        continue
            
            # Read the ZIP file
            with open(zip_path, 'rb') as f:
                zip_content = f.read()
            
            # Generate ZIP filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"batch_transcripts_{timestamp}.zip"
            
            return zip_content, zip_filename, generated_count


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
                'Access-Control-Allow-Headers': 'Content-Type'
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
            excel_content = form_parts.get('students_excel', b'')
            author_info_content = form_parts.get('author_info', b'').decode('utf-8')
            
            # Parse author YAML
            author_info_data = yaml.safe_load(author_info_content) if author_info_content else None
            
            if not excel_content or not author_info_data:
                raise ValueError("Missing required data: students_excel or author_info")
                
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Error parsing uploaded files: {str(e)}'})
            }
        
        # Generate batch transcripts using your existing system
        generator = BatchTranscriptGenerator()
        zip_content, zip_filename, generated_count = generator.generate_batch_transcripts_from_excel(
            excel_content, author_info_data
        )
        
        # Encode ZIP as base64
        zip_base64 = base64.b64encode(zip_content).decode('utf-8')
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({
                'success': True,
                'zip_data': zip_base64,
                'filename': zip_filename,
                'generated_count': generated_count,
                'message': f'Successfully generated {generated_count} transcripts'
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