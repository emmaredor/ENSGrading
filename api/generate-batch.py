"""
Vercel Serverless Function for Batch Student Transcript Generation
Uses the existing ENSGrading Python modules directly
"""

import json
import yaml
import tempfile
import os
import sys
import base64
import zipfile
from io import BytesIO
from datetime import datetime

# Add the parent directory to the Python path to access existing modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

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


def handler(request):
    """
    Vercel serverless function handler for batch student transcript generation.
    
    Expected POST request with multipart/form-data containing:
    - students_excel: Excel file with student data
    - author_info: YAML file content
    """
    
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
        # Parse the multipart form data
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
        
        # Get the request body
        body = request.get('body', '')
        if isinstance(body, str):
            body = body.encode('utf-8')
        
        # Parse form data
        form_data = parse_multipart_form_data(body, content_type)
        
        # Validate required files
        required_files = ['students_excel', 'author_info']
        for file_key in required_files:
            if file_key not in form_data:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': f'Missing required file: {file_key}'})
                }
        
        # Initialize transcript generator
        generator = BatchTranscriptGenerator()
        
        # Parse author data
        try:
            author_data = yaml.safe_load(form_data['author_info'])
        except yaml.YAMLError as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Invalid author YAML format: {str(e)}'})
            }
        
        # Process Excel file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save Excel file temporarily
            excel_path = os.path.join(temp_dir, 'students.xlsx')
            excel_content = form_data['students_excel']
            if isinstance(excel_content, str):
                excel_content = excel_content.encode('latin1')
            
            with open(excel_path, 'wb') as f:
                f.write(excel_content)
            
            # Load students from Excel
            try:
                students_data = generator.excel_loader.load_students_from_excel(excel_path)
            except Exception as e:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': f'Error processing Excel file: {str(e)}'})
                }
            
            if not students_data:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'No valid student data found in Excel file'})
                }
            
            # Load text templates
            text_templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'text.json')
            with open(text_templates_path, 'r', encoding='utf-8') as f:
                text_templates = json.load(f)
            
            # Generate PDFs for all students
            pdf_files = []
            student_names = []
            
            for student_entry in students_data:
                try:
                    # Combine student and author data
                    combined_data = generator.text_formatter.combine_student_author_data(
                        {'student': student_entry['student_info']},
                        {'author': author_data.get('author', author_data)}
                    )
                    
                    # Validate grades data
                    grades_data = student_entry['grades']
                    is_valid, errors = generator.grade_validator.validate_grades_data(grades_data)
                    if not is_valid:
                        continue  # Skip invalid students
                    
                    # Format text templates
                    formatted_texts = generator.text_formatter.format_all_templates(combined_data, text_templates)
                    
                    # Generate PDF
                    output_filename = f"{combined_data['student']['firstname']}_{combined_data['student']['name']}_transcript.pdf"
                    output_path = os.path.join(temp_dir, output_filename)
                    
                    generator.pdf_generator.generate_transcript(
                        formatted_texts, combined_data, grades_data, output_path
                    )
                    
                    pdf_files.append(output_path)
                    student_names.append(f"{combined_data['student']['firstname']} {combined_data['student']['name']}")
                    
                except Exception as e:
                    # Log error but continue with other students
                    continue
            
            if not pdf_files:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'No transcripts could be generated'})
                }
            
            # Create ZIP file
            zip_buffer = BytesIO()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"transcripts_batch_{timestamp}.zip"
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for pdf_path in pdf_files:
                    pdf_filename = os.path.basename(pdf_path)
                    zip_file.write(pdf_path, pdf_filename)
            
            zip_buffer.seek(0)
            zip_content = zip_buffer.read()
            zip_base64 = base64.b64encode(zip_content).decode('utf-8')
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({
                    'success': True,
                    'filename': zip_filename,
                    'zip_data': zip_base64,
                    'generated_count': len(pdf_files),
                    'student_names': student_names
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


def parse_multipart_form_data(body, content_type):
    """
    Simplified multipart form data parser.
    """
    # Extract boundary from content type
    boundary = None
    for part in content_type.split(';'):
        if 'boundary=' in part:
            boundary = part.split('boundary=')[1].strip()
            break
    
    if not boundary:
        raise ValueError("No boundary found in multipart data")
    
    # Split by boundary
    parts = body.split(f'--{boundary}'.encode())
    form_data = {}
    
    for part in parts[1:-1]:  # Skip first empty part and last closing part
        if not part.strip():
            continue
        
        # Split headers and content
        header_end = part.find(b'\r\n\r\n')
        if header_end == -1:
            continue
        
        headers = part[:header_end].decode('utf-8')
        content = part[header_end + 4:].rstrip(b'\r\n')
        
        # Extract field name from Content-Disposition header
        name = None
        for line in headers.split('\r\n'):
            if 'Content-Disposition:' in line and 'name=' in line:
                name_part = line.split('name=')[1]
                name = name_part.split(';')[0].strip('"')
                break
        
        if name:
            if 'filename=' in headers:
                # Binary file data
                form_data[name] = content
            else:
                # Text data
                form_data[name] = content.decode('utf-8')
    
    return form_data


# Vercel requires a default export for the handler
default = handler