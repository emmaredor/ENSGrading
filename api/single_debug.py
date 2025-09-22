from http.server import BaseHTTPRequestHandler
import json
import yaml
import base64
import os
import sys
import tempfile
from datetime import datetime
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
            # Read content length
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Get content type
            content_type = self.headers.get('Content-Type', '')
            
            # For now, let's just test that we can receive the request
            # and return a successful response without processing
            self.send_success_response({
                'success': True,
                'message': 'Function is working! Received POST request.',
                'content_type': content_type,
                'content_length': content_length,
                'note': 'This is a test response. PDF generation will be implemented once basic function works.'
            })
            
        except Exception as e:
            # Send detailed error information for debugging
            error_details = {
                'error': str(e),
                'traceback': traceback.format_exc(),
                'type': type(e).__name__
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
        self.wfile.write(json.dumps(data).encode())
    
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
            
        self.wfile.write(json.dumps(response_data).encode())