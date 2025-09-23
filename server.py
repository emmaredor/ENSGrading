"""
Web server entry point for Railway deployment
"""
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add the current directory to the Python path to access existing modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the handlers from both APIs
from api.single import handler as SingleHandler
from api.batch import handler as BatchHandler


class MainHandler(BaseHTTPRequestHandler):
    """Main handler that routes requests to appropriate API handlers"""
    
    def _add_cors_headers(self):
        """Add CORS headers to any response"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self._add_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests - serve index.html for root path"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/' or parsed_path.path == '':
            # Serve index.html for health check and main page
            try:
                with open('index.html', 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self._add_cors_headers()
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except FileNotFoundError:
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self._add_cors_headers()
                self.end_headers()
                self.wfile.write(b'ENS Grading System API is running!')
        else:
            # For any other GET request, return 404
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self._add_cors_headers()
            self.end_headers()
            self.wfile.write(b'Not Found - Use POST /api/single or /api/batch for transcript generation')
    
    def do_POST(self):
        """Route POST requests to appropriate API handlers"""
        parsed_path = urlparse(self.path)
        
        try:
            if parsed_path.path == '/api/single':
                # Delegate to single transcript handler
                single_handler = SingleHandler(self.request, self.client_address, self.server)
                single_handler.setup()
                single_handler.do_POST()
                single_handler.finish()
            elif parsed_path.path == '/api/batch':
                # Delegate to batch transcript handler  
                batch_handler = BatchHandler(self.request, self.client_address, self.server)
                batch_handler.setup()
                batch_handler.do_POST()
                batch_handler.finish()
            else:
                # Unknown endpoint
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self._add_cors_headers()
                self.end_headers()
                import json
                self.wfile.write(json.dumps({'error': 'Endpoint not found. Use /api/single or /api/batch'}).encode())
        except Exception as e:
            # Handle any uncaught exceptions with proper CORS headers
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._add_cors_headers()
            self.end_headers()
            import json
            self.wfile.write(json.dumps({'error': f'Internal server error: {str(e)}'}).encode())
def run_server():
    """Run the HTTP server for Railway deployment"""
    port = int(os.environ.get('PORT', 8080))
    server_address = ('0.0.0.0', port)
    
    print(f"Starting server on port {port}...")
    httpd = HTTPServer(server_address, MainHandler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()