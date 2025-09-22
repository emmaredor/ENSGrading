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

# Import the API handlers
from api.single import handler as SingleHandler
from api.batch import handler as BatchHandler

class MainHandler(BaseHTTPRequestHandler):
    """Main handler that routes to appropriate API endpoints"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests for all endpoints"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With, Accept, Origin')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests - serve index.html for root path"""
        parsed_path = urlparse(self.path)
        print(f"📥 GET request: {self.path}")
        
        if parsed_path.path == '/' or parsed_path.path == '':
            # Serve index.html for health check and main page
            try:
                with open('index.html', 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
                print("✅ Served index.html")
            except FileNotFoundError:
                # Fallback response for health check
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                fallback_html = '''<!DOCTYPE html>
<html><head><title>ENS Grading System API</title></head>
<body>
<h1>🎓 ENS Grading System API</h1>
<p>✅ Server is running successfully!</p>
<h2>Available Endpoints:</h2>
<ul>
<li>POST /api/single - Generate single student transcript</li>
<li>POST /api/batch - Generate batch transcripts from Excel</li>
</ul>
<p><em>Health check passed ✓</em></p>
</body></html>'''
                self.wfile.write(fallback_html.encode('utf-8'))
                print("✅ Served fallback health check page")
        elif parsed_path.path == '/health':
            # Simple health check endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            health_response = '{"status": "healthy", "service": "ENS Grading System API", "endpoints": ["/api/single", "/api/batch"]}'
            self.wfile.write(health_response.encode('utf-8'))
            print("✅ Health check endpoint called")
        else:
            # For any other GET request, return 404
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'Not Found - Use POST /api/single or /api/batch for transcript generation')
            print(f"❌ 404 for path: {self.path}")
    
    def do_POST(self):
        """Route POST requests to appropriate API handlers"""
        parsed_path = urlparse(self.path)
        print(f"📮 POST request: {self.path}")
        
        if parsed_path.path == '/api/single':
            print("🔄 Routing to single transcript API")
            # Route to single transcript API
            single_handler = SingleHandler()
            # Copy request attributes to the handler
            single_handler.rfile = self.rfile
            single_handler.wfile = self.wfile
            single_handler.headers = self.headers
            single_handler.send_response = self.send_response
            single_handler.send_header = self.send_header
            single_handler.end_headers = self.end_headers
            single_handler.do_POST()
            
        elif parsed_path.path == '/api/batch':
            print("🔄 Routing to batch transcript API")
            # Route to batch transcript API
            batch_handler = BatchHandler()
            # Copy request attributes to the handler
            batch_handler.rfile = self.rfile
            batch_handler.wfile = self.wfile
            batch_handler.headers = self.headers
            batch_handler.send_response = self.send_response
            batch_handler.send_header = self.send_header
            batch_handler.end_headers = self.end_headers
            batch_handler.do_POST()
            
        else:
            # Unknown endpoint
            print(f"❌ Unknown POST endpoint: {self.path}")
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"error": "API endpoint not found. Use /api/single or /api/batch"}')

def run_server():
    """Run the HTTP server for Railway deployment"""
    port = int(os.environ.get('PORT', 8080))
    server_address = ('0.0.0.0', port)
    
    print(f"Starting ENS Grading System server...")
    print(f"Port: {port}")
    print(f"Address: {server_address}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}")
    
    # Check if required files exist
    required_files = ['assets/text.json', 'assets/logo.png', 'index.html']
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ Found: {file_path}")
        else:
            print(f"⚠️  Missing: {file_path}")
    
    try:
        httpd = HTTPServer(server_address, MainHandler)
        print(f"🚀 Server successfully bound to {server_address}")
        print("Available endpoints:")
        print("  GET  / - Health check and info page")
        print("  POST /api/single - Single transcript generation")
        print("  POST /api/batch - Batch transcript generation")
        print("🟢 Server is ready to accept connections...")
        
        httpd.serve_forever()
        
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"❌ Port {port} is already in use")
        else:
            print(f"❌ Network error: {e}")
        raise
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    run_server()