#!/usr/bin/env python3
"""
Simple token server for LiveKit frontend integration
"""

import os
import time
import jwt
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import logging

logger = logging.getLogger(__name__)

class TokenHandler(BaseHTTPRequestHandler):
    """HTTP handler for token generation requests"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests for token generation"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/token':
            # Parse query parameters
            params = parse_qs(parsed_path.query)
            room = params.get('room', ['voice-agent-room'])[0]
            identity = params.get('identity', [f'user-{int(time.time())}'])[0]
            name = params.get('name', ['User'])[0]
            
            token = self.generate_token(room, identity, name)
            
            if token:
                self.send_json_response({'token': token, 'success': True})
            else:
                self.send_json_response({'error': 'Failed to generate token', 'success': False}, 500)
        
        elif parsed_path.path == '/check':
            # Health check endpoint
            self.send_json_response({'status': 'ok', 'service': 'token-server'})
        
        else:
            self.send_json_response({'error': 'Not found'}, 404)
    
    def do_POST(self):
        """Handle POST requests for token generation"""
        if self.path == '/api/token':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                room = data.get('room', 'voice-agent-room')
                identity = data.get('identity', f'user-{int(time.time())}')
                name = data.get('name', 'User')
                
                token = self.generate_token(room, identity, name)
                
                if token:
                    self.send_json_response({'token': token, 'success': True})
                else:
                    self.send_json_response({'error': 'Failed to generate token', 'success': False}, 500)
                    
            except Exception as e:
                logger.error(f"Error processing POST request: {e}")
                self.send_json_response({'error': 'Invalid request', 'success': False}, 400)
        else:
            self.send_json_response({'error': 'Not found'}, 404)
    
    def generate_token(self, room_name, identity, name):
        """Generate LiveKit token"""
        try:
            api_key = os.getenv("LIVEKIT_API_KEY")
            api_secret = os.getenv("LIVEKIT_API_SECRET")
            
            if not api_key or not api_secret:
                logger.error("LiveKit credentials not found")
                return None
            
            now = int(time.time())
            exp = now + (24 * 60 * 60)  # 24 hours
            
            claim = {
                "iss": api_key,
                "nbf": now,
                "exp": exp,
                "sub": identity,
                "video": {
                    "room": room_name,
                    "room_join": True,
                    "can_publish": True,
                    "can_subscribe": True,
                    "can_publish_data": True,
                },
                "metadata": name
            }
            
            token = jwt.encode(claim, api_secret, algorithm="HS256")
            logger.info(f"Generated token for user {identity} in room {room_name}")
            return token
            
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            return None
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data)
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use proper logging"""
        logger.info(f"{self.address_string()} - {format % args}")

class TokenServer:
    """Simple token server for LiveKit integration"""
    
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the token server in a separate thread"""
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), TokenHandler)
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            logger.info(f"Token server started on port {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start token server: {e}")
            return False
    
    def stop(self):
        """Stop the token server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Token server stopped")

def main():
    """Run the token server standalone"""
    import dotenv
    dotenv.load_dotenv()
    
    logging.basicConfig(level=logging.INFO)
    
    port = int(os.getenv('TOKEN_SERVER_PORT', 8080))
    server = TokenServer(port)
    
    if server.start():
        print(f"Token server running on http://0.0.0.0:{port}")
        print("Endpoints:")
        print(f"  GET  http://0.0.0.0:{port}/api/token?room=test&identity=user1&name=User")
        print(f"  POST http://0.0.0.0:{port}/api/token")
        print(f"  GET  http://0.0.0.0:{port}/check")
        print("\nPress Ctrl+C to stop...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping server...")
            server.stop()
    else:
        print("Failed to start token server")

if __name__ == "__main__":
    main()