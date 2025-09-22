"""
Vercel Serverless Function for Single Student Transcript Generation
Uses the existing ENSGrading Python modules directly
"""

import json
import yaml
import tempfile
import os
import sys
import base64

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


def handler(request):
    """
    Vercel serverless function handler for single student transcript generation.
    
    Expected POST request with multipart/form-data containing:
    - student_info: YAML file content
    - author_info: YAML file content  
    - grades: JSON file content
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
        required_files = ['student_info', 'author_info', 'grades']
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
        generator = TranscriptGenerator()
        
        # Parse uploaded files
        try:
            student_data = yaml.safe_load(form_data['student_info'])
            author_data = yaml.safe_load(form_data['author_info'])
            grades_data = json.loads(form_data['grades'])
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Invalid file format: {str(e)}'})
            }
        
        # Combine student and author data
        combined_data = generator.text_formatter.combine_student_author_data(
            {'student': student_data.get('student', student_data)},
            {'author': author_data.get('author', author_data)}
        )
        
        # Validate required fields
        if not generator.text_formatter.validate_required_fields(combined_data):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing required fields in student/author data'})
            }
        
        # Validate grades data
        is_valid, errors = generator.grade_validator.validate_grades_data(grades_data)
        if not is_valid:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Invalid grades data: {"; ".join(errors)}'})
            }
        
        # Load text templates
        text_templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'text.json')
        with open(text_templates_path, 'r', encoding='utf-8') as f:
            text_templates = json.load(f)
        
        # Format text templates
        formatted_texts = generator.text_formatter.format_all_templates(combined_data, text_templates)
        
        # Generate PDF in temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_filename = f"{combined_data['student']['firstname']}_{combined_data['student']['name']}_transcript.pdf"
            output_path = os.path.join(temp_dir, output_filename)
            
            # Generate PDF
            generator.pdf_generator.generate_transcript(
                formatted_texts, combined_data, grades_data, output_path
            )
            
            # Read the generated PDF
            with open(output_path, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
            
            # Encode PDF as base64 for response
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
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
                    'filename': output_filename,
                    'pdf_data': pdf_base64,
                    'student_name': f"{combined_data['student']['firstname']} {combined_data['student']['name']}"
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
            form_data[name] = content.decode('utf-8')
    
    return form_data


# Vercel requires a default export for the handler
default = handler