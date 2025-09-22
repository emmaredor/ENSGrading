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
            
            # Step 2: Read request data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            content_type = self.headers.get('Content-Type', '')
            
            # Step 3: Test imports
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
            
            # Step 4: Test ENS module imports
            module_status = "❌ Module import not tested yet"
            modules_imported = {}
            try:
                # Add the parent directory to the Python path
                current_dir = os.path.dirname(__file__)
                parent_dir = os.path.dirname(current_dir)
                sys.path.insert(0, parent_dir)
                
                # Try importing the modules one by one
                try:
                    from data_loader import DataLoader
                    modules_imported['DataLoader'] = "✅"
                except Exception as e:
                    modules_imported['DataLoader'] = f"❌ {str(e)}"
                
                try:
                    from text_formatter import TextFormatter
                    modules_imported['TextFormatter'] = "✅"
                except Exception as e:
                    modules_imported['TextFormatter'] = f"❌ {str(e)}"
                
                try:
                    from pdf_generator import TranscriptPDFGenerator
                    modules_imported['TranscriptPDFGenerator'] = "✅"
                except Exception as e:
                    modules_imported['TranscriptPDFGenerator'] = f"❌ {str(e)}"
                
                try:
                    from grades_processor import GradeValidator
                    modules_imported['GradeValidator'] = "✅"
                except Exception as e:
                    modules_imported['GradeValidator'] = f"❌ {str(e)}"
                
                # Check if all modules imported successfully
                failed_modules = [k for k, v in modules_imported.items() if "❌" in v]
                if not failed_modules:
                    module_status = "✅ All ENS modules imported successfully"
                else:
                    module_status = f"❌ Failed modules: {', '.join(failed_modules)}"
                    
            except Exception as e:
                module_status = f"❌ General module import error: {str(e)}"
            
            # Step 5: Test form data parsing
            form_parsing_status = "❌ Not tested"
            boundary_info = "Not found"
            form_fields = {}
            
            if 'multipart/form-data' in content_type:
                try:
                    # Extract boundary
                    boundary = None
                    for part in content_type.split(';'):
                        if 'boundary=' in part:
                            boundary = '--' + part.split('boundary=')[1].strip()
                            break
                    
                    if boundary:
                        boundary_info = f"Found: {boundary[:20]}..."
                        
                        # Simple form parsing
                        parts = post_data.split(boundary.encode())
                        
                        for i, part in enumerate(parts):
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
                                                form_fields[field_name] = f"Found {len(content)} bytes"
                                                
                                                # Try to parse the content
                                                if field_name in ['student_info', 'author_info']:
                                                    try:
                                                        yaml_data = yaml.safe_load(content.decode('utf-8'))
                                                        form_fields[field_name] += f" (Valid YAML with {len(yaml_data)} keys)"
                                                    except Exception as e:
                                                        form_fields[field_name] += f" (YAML parse error: {str(e)[:50]})"
                                                elif field_name == 'grades':
                                                    try:
                                                        json_data = json.loads(content.decode('utf-8'))
                                                        form_fields[field_name] += f" (Valid JSON with {len(json_data)} items)"
                                                    except Exception as e:
                                                        form_fields[field_name] += f" (JSON parse error: {str(e)[:50]})"
                                            break
                        
                        form_parsing_status = f"✅ Found {len(form_fields)} form fields"
                    else:
                        form_parsing_status = "❌ No boundary found in multipart data"
                        
                except Exception as e:
                    form_parsing_status = f"❌ Form parsing error: {str(e)}"
            else:
                form_parsing_status = f"❌ Not multipart data: {content_type}"
            
            # Return comprehensive diagnostic information
            self.send_success_response({
                'success': True,
                'message': 'Comprehensive diagnostic test completed',
                'diagnostics': {
                    'basic_info': {
                        'content_type': content_type,
                        'content_length': content_length,
                        'python_version': sys.version,
                        'current_directory': os.getcwd(),
                        'file_location': __file__ if '__file__' in globals() else 'unknown'
                    },
                    'imports': {
                        'standard_libraries': import_status,
                        'ens_modules': modules_imported,
                        'overall_module_status': module_status
                    },
                    'form_processing': {
                        'boundary_info': boundary_info,
                        'parsing_status': form_parsing_status,
                        'found_fields': form_fields
                    },
                    'environment': {
                        'python_path_entries': sys.path[:5],
                        'available_files': os.listdir('.') if os.path.exists('.') else 'Cannot list directory'
                    }
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
            self.send_error_response(500, f'Diagnostic error: {str(e)}', error_details)
    
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