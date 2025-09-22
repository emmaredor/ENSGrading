from http.server import BaseHTTPRequestHandler
import json
import sys
import os

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
        self.end_headers()
        
    def do_GET(self):
        try:
            # Test basic imports first
            import_results = {}
            
            # Test standard library imports
            try:
                import yaml
                import_results['yaml'] = "✅ Success"
            except ImportError as e:
                import_results['yaml'] = f"❌ Failed: {str(e)}"
            
            try:
                import pandas
                import_results['pandas'] = "✅ Success"
            except ImportError as e:
                import_results['pandas'] = f"❌ Failed: {str(e)}"
            
            try:
                import reportlab
                import_results['reportlab'] = "✅ Success"
            except ImportError as e:
                import_results['reportlab'] = f"❌ Failed: {str(e)}"
            
            try:
                import openpyxl
                import_results['openpyxl'] = "✅ Success"
            except ImportError as e:
                import_results['openpyxl'] = f"❌ Failed: {str(e)}"
            
            # Test path setup
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            
            # Test custom module imports
            custom_imports = {}
            sys.path.insert(0, parent_dir)
            
            try:
                from data_loader import DataLoader
                custom_imports['data_loader'] = "✅ Success"
            except ImportError as e:
                custom_imports['data_loader'] = f"❌ Failed: {str(e)}"
            
            try:
                from text_formatter import TextFormatter
                custom_imports['text_formatter'] = "✅ Success"
            except ImportError as e:
                custom_imports['text_formatter'] = f"❌ Failed: {str(e)}"
            
            try:
                from pdf_generator import TranscriptPDFGenerator
                custom_imports['pdf_generator'] = "✅ Success"
            except ImportError as e:
                custom_imports['pdf_generator'] = f"❌ Failed: {str(e)}"
            
            try:
                from grades_processor import GradeValidator
                custom_imports['grades_processor'] = "✅ Success"
            except ImportError as e:
                custom_imports['grades_processor'] = f"❌ Failed: {str(e)}"
            
            # Prepare response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {
                'status': 'success',
                'message': 'Import test completed',
                'environment': {
                    'python_version': sys.version,
                    'current_directory': current_dir,
                    'parent_directory': parent_dir,
                    'python_path': sys.path[:5],  # First 5 entries
                    'working_directory': os.getcwd(),
                    'file_location': __file__ if '__file__' in globals() else 'unknown'
                },
                'dependency_imports': import_results,
                'custom_module_imports': custom_imports,
                'files_in_parent': os.listdir(parent_dir) if os.path.exists(parent_dir) else 'Directory not found',
                'files_in_current': os.listdir(current_dir) if os.path.exists(current_dir) else 'Directory not found'
            }
            
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                'status': 'error',
                'message': str(e),
                'type': type(e).__name__
            }
            
            self.wfile.write(json.dumps(error_response).encode())