"""
Health Check Endpoint for Railway
Simple HTTP server for Railway health checks
"""

import asyncio
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os

logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check handler for Railway."""
    
    def do_GET(self):
        """Handle GET requests for health checks."""
        
        if self.path == '/health':
            # Health check endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            health_data = {
                'status': 'healthy',
                'service': 'caresetu-voice-agent',
                'environment': os.getenv('RAILWAY_ENVIRONMENT', 'unknown'),
                'port': os.getenv('PORT', '8080')
            }
            
            self.wfile.write(json.dumps(health_data).encode())
            
        elif self.path == '/':
            # Root endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'CareSetu Voice Agent - Railway Deployment')
            
        else:
            # Not found
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass

class HealthCheckServer:
    """Health check server for Railway deployment."""
    
    def __init__(self, port: int = None):
        """Initialize health check server."""
        self.port = port or int(os.getenv('PORT', 8080))
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the health check server."""
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), HealthCheckHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            logger.info(f"✅ Health check server started on port {self.port}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start health check server: {e}")
            return False
    
    def stop(self):
        """Stop the health check server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("🛑 Health check server stopped")

# Global health check server instance
health_server = None

def start_health_check_server(port: int = None):
    """Start the global health check server."""
    global health_server
    
    if health_server is None:
        health_server = HealthCheckServer(port)
        return health_server.start()
    
    return True

def stop_health_check_server():
    """Stop the global health check server."""
    global health_server
    
    if health_server:
        health_server.stop()
        health_server = None

if __name__ == "__main__":
    # Test the health check server
    import time
    
    print("🏥 Testing Railway Health Check Server")
    
    server = HealthCheckServer(8080)
    if server.start():
        print("✅ Health check server started on http://localhost:8080")
        print("🔍 Test endpoints:")
        print("   - http://localhost:8080/health")
        print("   - http://localhost:8080/")
        
        try:
            time.sleep(30)  # Run for 30 seconds
        except KeyboardInterrupt:
            pass
        
        server.stop()
        print("🛑 Health check server stopped")
    else:
        print("❌ Failed to start health check server")