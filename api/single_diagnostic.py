from http.server import BaseHTTPRequestHandler
import json
import traceback

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
            # Step 1: Test basic functionality
            self.log_message("POST request received")
            
            # Step 2: Test imports
            try:
                import yaml
                import base64
                import os
                import sys
                import tempfile
                from datetime import datetime
                import_status = "✅ Basic imports successful"
            except Exception as e:
                import_status = f"❌ Import error: {str(e)}"
            
            # Step 3: Test ENS module imports
            module_status = "❌ Module import not tested yet"
            try:
                # Add the parent directory to the Python path
                current_dir = os.path.dirname(__file__)
                parent_dir = os.path.dirname(current_dir)
                sys.path.insert(0, parent_dir)
                
                # Try importing the modules
                from data_loader import DataLoader
                from text_formatter import TextFormatter
                from pdf_generator import TranscriptPDFGenerator
                from grades_processor import GradeValidator
                
                module_status = "✅ ENS modules imported successfully"
            except Exception as e:
                module_status = f"❌ ENS module import error: {str(e)}"
            
            # Step 4: Test form data parsing
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            content_type = self.headers.get('Content-Type', '')
            
            parsing_status = f"Content-Type: {content_type}, Content-Length: {content_length}"
            
            # Return diagnostic information
            self.send_success_response({
                'success': True,
                'message': 'Diagnostic test completed',
                'diagnostics': {
                    'import_status': import_status,
                    'module_status': module_status,
                    'parsing_status': parsing_status,
                    'python_path': sys.path[:3],  # First 3 entries
                    'current_directory': os.getcwd(),
                    'file_location': __file__ if '__file__' in globals() else 'unknown'
                }
            })
            
        except Exception as e:
            # Send detailed error information for debugging
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                'type': type(e).__name__,
                'python_version': sys.version
            }
            self.send_error_response(500, f'Server error: {str(e)}', error_details)
    
    def send_success_response(self, data):
        """Send a successful JSON response with CORS headers."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_error_response(self, status_code, message, details=None):
        """Send an error JSON response with CORS headers."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
        self.end_headers()
        
        response_data = {'error': message}
        if details:
            response_data['details'] = details
            
        self.wfile.write(json.dumps(response_data, indent=2).encode())