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
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
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
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except FileNotFoundError:
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'ENS Grading System API is running!')
        else:
            # For any other GET request, return 404
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'Not Found - Use POST /api/single or /api/batch for transcript generation')
    
    def do_POST(self):
        """Route POST requests to appropriate API handlers"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/single':
            # Delegate to single transcript handler
            single_handler = SingleHandler()
            # Copy necessary attributes
            single_handler.request = self.request
            single_handler.client_address = self.client_address
            single_handler.server = self.server
            single_handler.rfile = self.rfile
            single_handler.wfile = self.wfile
            single_handler.headers = self.headers
            single_handler.command = self.command
            single_handler.path = self.path
            single_handler.do_POST()
        elif parsed_path.path == '/api/batch':
            # Delegate to batch transcript handler  
            batch_handler = BatchHandler()
            # Copy necessary attributes
            batch_handler.request = self.request
            batch_handler.client_address = self.client_address
            batch_handler.server = self.server
            batch_handler.rfile = self.rfile
            batch_handler.wfile = self.wfile
            batch_handler.headers = self.headers
            batch_handler.command = self.command
            batch_handler.path = self.path
            batch_handler.do_POST()
        else:
            # Unknown endpoint
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            import json
            self.wfile.write(json.dumps({'error': 'Endpoint not found. Use /api/single or /api/batch'}).encode())
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