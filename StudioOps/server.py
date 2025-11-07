#!/usr/bin/env python3
"""
Simple HTTP Server for StudioOps Dashboard
==========================================

This script provides a lightweight HTTP server to run the StudioOps dashboard
locally. It serves the files on localhost:8000 by default.

Usage:
    python3 server.py [port]

Examples:
    python3 server.py          # Starts server on port 8000
    python3 server.py 3000     # Starts server on port 3000

Requirements:
    - Python 3.x (built-in http.server module)
    - No external dependencies required!

Once started, open your browser to:
    http://localhost:8000/index.html      (for modular ES6 version)
    http://localhost:8000/dashboard.html  (for bundled local version)
    http://localhost:8000/start.html      (for smart launcher)
"""

import http.server
import socketserver
import sys
import os

# Default port
DEFAULT_PORT = 8000

# Get port from command line argument or use default
port = DEFAULT_PORT
if len(sys.argv) > 1:
    try:
        port = int(sys.argv[1])
    except ValueError:
        print(f"Invalid port number: {sys.argv[1]}")
        print("Using default port:", DEFAULT_PORT)
        port = DEFAULT_PORT

# Change to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Define handler
Handler = http.server.SimpleHTTPRequestHandler

# Add custom headers to allow CORS and ES6 modules
class CustomHandler(Handler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

        # Ensure JavaScript modules are served with correct MIME type
        if self.path.endswith('.js'):
            self.send_header('Content-Type', 'application/javascript')

        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

# Create server
with socketserver.TCPServer(("", port), CustomHandler) as httpd:
    print("=" * 70)
    print("  StudioOps Dashboard Server")
    print("=" * 70)
    print(f"\n✅ Server started successfully!")
    print(f"\n📍 Server running at:")
    print(f"   http://localhost:{port}/")
    print(f"\n📄 Available pages:")
    print(f"   http://localhost:{port}/start.html       - Smart launcher (recommended)")
    print(f"   http://localhost:{port}/index.html       - ES6 modular version")
    print(f"   http://localhost:{port}/dashboard.html   - Bundled single-file version")
    print(f"\n💡 Tips:")
    print(f"   - Press Ctrl+C to stop the server")
    print(f"   - The server will automatically reload if you refresh your browser")
    print(f"   - All files are served from: {os.getcwd()}")
    print(f"\n🔧 To use a different port: python3 server.py [port]")
    print("=" * 70)
    print(f"\n🚀 Serving HTTP on port {port}...\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user.")
        print("=" * 70)
