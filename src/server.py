"""
Enhanced TCP Server for pytest-viu-design plugin.
Implements JSON-RPC style protocol with connection management, security, and logging.
"""
import argparse
import json
import logging
import os
import socket
import threading
import time
from typing import Any, Dict, TypedDict

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(thread)d - %(name)s %(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('log/server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServerConfig(TypedDict, total=False):
    """Type definition for server configuration parameters."""
    host: str
    port: int
    max_connections: int
    heartbeat_interval: int
    token: str

class SimpleTCPServer:
    def __init__(self, config: ServerConfig):
        """Initialize enhanced TCP server with configuration."""
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8080)
        self.max_connections = config.get('max_connections', 100)
        self.heartbeat_interval = config.get('heartbeat_interval', 30)  # seconds
        self.token = config.get('token', '')  # Authentication token
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.running = False
        self.active_connections: Dict[socket.socket, float] = {}  # Track client last activity time
        self.timeout_clients: list[socket.socket] = []
        self.heartbeat_thread: threading.Thread = None
        self.logger = logger

    def handle_client(self, client_socket: socket.socket):
        """Handle client communication with JSON-RPC style protocol."""
        client_addr = client_socket.getpeername()
        self.logger.info(f"New client connection from {client_addr}")
        
        try:
            while self.running:
                if client_socket in self.timeout_clients:
                    self.logger.warning(f"{client_addr} timeout")
                    response = {"type": "response", "id": 10001, "command": "disconnect"}
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                    self.timeout_clients.remove(client_socket)
                    break

                data = client_socket.recv(1024).decode('utf-8').strip()
                if not data:
                    break  # Client closed connection
                
                # Update last activity time
                self.active_connections[client_socket] = time.time()
                
                # Parse JSON message
                try:
                    message = json.loads(data)
                    self.logger.info(f"Client {client_addr} request: {message}")
                except json.JSONDecodeError as e:
                    response = {"type": "error", "message": f"Invalid JSON: {str(e)}"}
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                    continue
                
                # Authentication check
                if self.token and message.get('token') != self.token:
                    response = {"type": "error", "message": "Unauthorized: Invalid token"}
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                    continue
                
                # Process message types
                response = self._process_message(message)
                client_socket.sendall(json.dumps(response).encode('utf-8'))
                
        except Exception as e:
            self.logger.error(f"Client error {client_addr}: {str(e)}", exc_info=True)
        finally:
            self.logger.info(f"Closing connection with {client_addr}")
            del self.active_connections[client_socket]
            client_socket.close()

    def _process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming JSON messages and generate appropriate responses."""
        message_type = message.get('type')
        
        if message_type == 'request':
            command = message.get('command')
            request_id = message.get('id')
            
            if command == 'get_status':
                response = {"type": "response", "id": request_id, "status": "ok", "server_time": time.time()}
            elif command == 'health_check':
                response = {"type": "response", "id": request_id, "status": "healthy"}
            elif command == 'echo_with_timestamp':
                # Extract client message and timestamp
                client_text = message.get('text', '')
                #client_timestamp = message.get('client_timestamp', '')
                
                # Generate server's timestamp (formatted as string)
                server_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Replace client timestamp with server's (or append if no placeholder)
                # Assume client text uses "[TIMESTAMP]" as placeholder, or we append server time
                
                dt = time.strftime("%Y-%m-%d %H:%M:%S")
                server_text = f"Server message at {dt}"
                response_text = f"{client_text} {server_text}"
            
                response = {
                    "type": "response",
                    "id": request_id,
                    "status": "ok",
                    # "client_text": client_text,
                    # "client_timestamp": client_timestamp,
                    "server_text": response_text,
                    "server_timestamp": server_timestamp
                }
            else:
                response = {"type": "error", "id": request_id, "message": f"Unknown command: {command}"}
        
        elif message_type == 'heartbeat':
            response = {"type": "heartbeat_ack"}
        else:
            response = {"type": "error", "message": f"Unknown message type: {message_type}"}
        self.logger.info(f'Server response: {response}')
        return response
    def _start_heartbeat_monitor(self):
        """Start background thread to monitor client heartbeats."""
        def monitor():
            while self.running:
                current_time = time.time()
                self.timeout_clients = [
                    sock for sock, last_active in self.active_connections.items()
                    if current_time - last_active > self.heartbeat_interval
                ]
                
                time.sleep(5)  # Check every 5 seconds
        
        self.heartbeat_thread = threading.Thread(target=monitor, daemon=True)
        self.heartbeat_thread.start()

    def start(self):
        """Start the enhanced TCP server."""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_connections)
            self.running = True
            self._start_heartbeat_monitor()
            
            self.logger.info(
                f"Server started on {self.host}:{self.port} | "
                f"Max connections: {self.max_connections} | "
                f"Heartbeat interval: {self.heartbeat_interval}s"
            )
            
            while self.running:
                client_socket, addr = self.server_socket.accept()
                client_addr = client_socket.getpeername()
                self.logger.info(f'Starting connection with {client_addr}')
                
                # Check connection limit
                if len(self.active_connections) >= self.max_connections:
                    self.logger.warning(f"Connection limit reached - rejecting {addr}")
                    client_socket.sendall(json.dumps({
                        "type": "error", 
                        "message": "Server busy: Max connections reached"
                    }).encode('utf-8'))
                    client_socket.close()
                    continue
                
                # Add to active connections
                self.active_connections[client_socket] = time.time()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True)
                client_thread.start()
                
        except Exception as e:
            self.logger.error(f"Server startup failed: {str(e)}", exc_info=True)
            self.stop()

    def stop(self):
        """Gracefully stop the server and clean up resources."""
        if not self.running:
            return
        
        self.logger.info("Stopping server...")
        self.running = False
        
        # Close all client connections
        for sock in list(self.active_connections.keys()):
            try:
                sock.close()
            except Exception as e:
                self.logger.error(f"Error closing client: {str(e)}")
        
        # Close server socket
        self.server_socket.close()
        self.logger.info("Server stopped successfully")

def load_config(config_path: str) -> ServerConfig:
    """Load server configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found - using defaults")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid config file: {str(e)}")
        return {}

def main():
    """Main entry point with command-line argument support."""
    parser = argparse.ArgumentParser(description='Enhanced TCP Server for pytest-viu-design')
    parser.add_argument('--host', help='Host address to bind (default: localhost)')
    parser.add_argument('--port', type=int, help='Port number to listen (default: 8080)')
    parser.add_argument('--config', default='configs/config.json', help='Path to configuration file')
    args = parser.parse_args()
    
    # Load configuration
    logger.info(f'args.config: {os.path.abspath(args.config)}')
    config = load_config(args.config)
    
    # Override config with command-line arguments
    if args.host:
        config['host'] = args.host
    if args.port:
        config['port'] = args.port
    
    # Start server
    server = SimpleTCPServer(config)
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

if __name__ == "__main__":
    main()