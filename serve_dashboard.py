#!/usr/bin/env python3
"""
Simple HTTP server to serve the dashboard HTML file
This fixes CORS issues when connecting to Supabase
"""
import http.server
import socketserver
import webbrowser
import os

PORT = 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    os.chdir('/Users/jeffreydebolt/Documents/cfo_forecast_refactored')
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🚀 Dashboard server running at http://localhost:{PORT}")
        print(f"📊 Open: http://localhost:{PORT}/weekly_dashboard_real_data.html")
        print("Press Ctrl+C to stop")
        
        # Auto-open browser
        webbrowser.open(f'http://localhost:{PORT}/weekly_dashboard_real_data.html')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")