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

# Import the existing handler from the API
from api.single_working import handler

class MainHandler(handler):
    """Extended handler that serves static files and API endpoints"""
    
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
                self.end_headers()
                self.wfile.write(b'ENS Grading System API is running!')
        else:
            # For any other GET request, return 404
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found - Use POST /api/single for transcript generation')

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