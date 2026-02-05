"""
Enhanced TCP Server for pytest-learn-multi-test-categories plugin.
Implements JSON-RPC style protocol with connection management, security, and logging.
"""
import argparse
import json5
import os
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

# 添加项目根目录到 Python 路径（用于直接运行脚本时）
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.log import load_config, logger


class ConnectionManager:
    """Thread-safe connection manager with status tracking"""
    def __init__(self, heartbeat_timeout=5):
        self.active_connections: Dict[socket.socket, Dict[str, Any]] = {}
        self.lock = threading.RLock()  # 使用可重入锁
        self.heartbeat_timeout = heartbeat_timeout
    
    def add_connection(self, client_socket: socket.socket, address: tuple):
        """Add a new connection with status tracking"""
        with self.lock:
            self.active_connections[client_socket] = {
                'address': address,
                'status': 'active',
                'last_active': time.time()
            }
            logger.debug(f"Added connection: {address}")
    
    def get_connection_status(self, client_socket: socket.socket) -> str:
        """Get connection status in a thread-safe manner"""
        with self.lock:
            if client_socket in self.active_connections:
                return self.active_connections[client_socket].get('status', 'active')
            return 'closed'
    
    def update_activity(self, client_socket: socket.socket):
        """Update last activity time for a connection"""
        with self.lock:
            if client_socket in self.active_connections:
                self.active_connections[client_socket]['last_active'] = time.time()
    
    def close_connection(self, client_socket: socket.socket, reason: str = "unknown"):
        """Safely close a connection with status tracking"""
        with self.lock:
            if client_socket not in self.active_connections:
                return
            
            # Mark as closing to prevent other threads from operating on it
            if self.active_connections[client_socket].get('status') != 'closing':
                self.active_connections[client_socket]['status'] = 'closing'
                
                try:
                    # Close the socket first
                    client_socket.close()
                    address = self.active_connections[client_socket]['address']
                    logger.info(f"Connection closed by manager: {address}, reason: {reason}")
                except Exception as e:
                    logger.debug(f"Error closing socket: {e}")
                finally:
                    # Remove from active connections
                    if client_socket in self.active_connections:
                        del self.active_connections[client_socket]
    
    def get_timeout_connections(self) -> list:
        """Get connections that have timed out"""
        current_time = time.time()
        timeout_connections = []
        
        with self.lock:
            for sock, info in list(self.active_connections.items()):
                if (current_time - info.get('last_active', 0) > self.heartbeat_timeout and
                    info.get('status') == 'active'):
                    timeout_connections.append(sock)
        
        return timeout_connections
    
    def get_connection_count(self) -> int:
        """Get current active connection count"""
        with self.lock:
            return len(self.active_connections)

class SimpleTCPServer:
    def __init__(self, config: Dict[str, Any]):
        """Initialize enhanced TCP server with configuration."""
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8080)
        self.max_connections = config.get('max_connections', 100)
        self.heartbeat_interval = config.get('heartbeat_interval', 5)  # seconds
        self.token = config.get('token', '')  # Authentication token
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.running = False
        self.connection_manager = ConnectionManager(self.heartbeat_interval)
        self.heartbeat_thread: Optional[threading.Thread] = None
        self.logger = logger

    def handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle client communication with JSON-RPC style protocol."""
        self.logger.info(f"New client connection from {address}")
        
        try:
            # Add connection to manager
            self.connection_manager.add_connection(client_socket, address)
            
            while self.running:
                # Check connection status before any operation
                status = self.connection_manager.get_connection_status(client_socket)
                if status in ['closing', 'closed'] or not self.running:
                    self.logger.debug(f"Connection status is {status}, exiting handler for {address}")
                    break
                
                try:
                    # Set timeout to allow status checking
                    client_socket.settimeout(0.5)  # 500ms
                    
                    data = client_socket.recv(1024)
                    if not data:
                        break  # Client closed connection
                    
                    # Update last activity time
                    self.connection_manager.update_activity(client_socket)
                    
                    # Parse JSON message
                    try:
                        message = json.loads(data.decode('utf-8'))
                        self.logger.info(f"Client {address} request: {message}")
                    except json.JSONDecodeError as e:
                        response = {"type": "error", "message": f"Invalid JSON: {str(e)}"}
                        client_socket.sendall(json.dumps(response).encode('utf-8'))
                        continue
                    
                    # Authentication check
                    if self.token and message.get('token') != self.token:
                        response = {"type": "error", "message": "Unauthorized: Invalid token"}
                        client_socket.sendall(json.dumps(response).encode('utf-8'))
                        continue
                    
                    # Process message
                    response = self._process_message(message)
                    client_socket.sendall(json.dumps(response).encode('utf-8'))
                    
                except socket.timeout:
                    # Normal timeout, continue to check status
                    continue
                except (ConnectionResetError, BrokenPipeError) as e:
                    self.logger.info(f"Client {address} disconnected: {e}")
                    break
                except OSError as e:
                    # Check for socket closed errors
                    if e.errno in (10038, 10053, 10054, 10058):  # Common socket closed errors
                        self.logger.debug(f"Socket closed for {address}: {e}")
                        break
                    else:
                        self.logger.error(f"Socket error for {address}: {e}")
                        break
                except Exception as e:
                    self.logger.error(f"Error handling client {address}: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Client error {address}: {str(e)}", exc_info=True)
        finally:
            self.logger.info(f"Closing connection with {address}")
            self.connection_manager.close_connection(client_socket, "handler_exit")

    def _process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming JSON messages and generate appropriate responses."""
        message_type = message.get('type')
        
        if message_type == 'request':
            command = message.get('command')
            request_id = message.get('id')
            
            if command == 'get_status':
                return {
                    "type": "response", 
                    "id": request_id, 
                    "status": "ok", 
                    "server_time": time.time(),
                    "connections": self.connection_manager.get_connection_count()
                }
            elif command == 'health_check':
                return {"type": "response", "id": request_id, "status": "healthy"}
            elif command == 'echo_with_timestamp':
                client_text = message.get('text', '')
                server_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                server_text = f"Server processed at {server_timestamp}"
                
                return {
                    "type": "response",
                    "id": request_id,
                    "status": "ok",
                    "original_text": client_text,
                    "server_response": f"{client_text} - {server_text}",
                    "server_timestamp": server_timestamp
                }
            else:
                return {"type": "error", "id": request_id, "message": f"Unknown command: {command}"}
        
        elif message_type == 'heartbeat':
            return {"type": "heartbeat_ack"}
        else:
            return {"type": "error", "message": f"Unknown message type: {message_type}"}

    def _start_heartbeat_monitor(self):
        """Start background thread to monitor client heartbeats."""
        def monitor():
            while self.running:
                try:
                    # Get timeout connections
                    timeout_connections = self.connection_manager.get_timeout_connections()
                    
                    # Close timeout connections
                    for sock in timeout_connections:
                        address = None
                        try:
                            address = sock.getpeername()
                        except:
                            pass
                        
                        self.logger.warning(f"Connection timeout: {address}")
                        self.connection_manager.close_connection(sock, "heartbeat_timeout")
                    
                    time.sleep(2)  # Check every 2 seconds
                    
                except Exception as e:
                    self.logger.error(f"Heartbeat monitor error: {e}")
                    time.sleep(5)  # Wait longer on error
        
        self.heartbeat_thread = threading.Thread(
            target=monitor, 
            name="HeartbeatMonitor",
            daemon=True
        )
        self.heartbeat_thread.start()

    def start(self):
        """Start the enhanced TCP server."""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_connections)
            self.server_socket.settimeout(1.0)  # Set accept timeout
            self.running = True
            
            self._start_heartbeat_monitor()
            
            self.logger.info(
                f"Server started on {self.host}:{self.port} | "
                f"Max connections: {self.max_connections} | "
                f"Heartbeat interval: {self.heartbeat_interval}s"
            )
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    client_addr = client_socket.getpeername()
                    self.logger.info(f'Starting connection with {client_addr}')
                    
                    # Check connection limit
                    if self.connection_manager.get_connection_count() >= self.max_connections:
                        self.logger.warning(f"Connection limit reached - rejecting {addr}")
                        client_socket.sendall(json.dumps({
                            "type": "error", 
                            "message": "Server busy: Max connections reached"
                        }).encode('utf-8'))
                        client_socket.close()
                        continue
                    
                    # Start client handler thread
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket, client_addr),
                        name=f"ClientHandler-{client_addr[1]}",
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue  # Normal timeout, continue loop
                except OSError as e:
                    if self.running:  # Only log if we're not shutting down
                        self.logger.error(f"Error accepting connection: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Server startup failed: {str(e)}", exc_info=True)
        finally:
            self.stop()

    def stop(self):
        """Gracefully stop the server and clean up resources."""
        if not self.running:
            return
        
        self.logger.info("Stopping server...")
        self.running = False
        
        # Close all client connections
        self.logger.info("Closing all client connections...")
        # We need to get a copy of the connections to avoid modification during iteration
        connections = list(self.connection_manager.active_connections.keys())
        for sock in connections:
            self.connection_manager.close_connection(sock, "server_shutdown")
        
        # Close server socket
        try:
            self.server_socket.close()
        except Exception as e:
            self.logger.error(f"Error closing server socket: {e}")
        
        self.logger.info("Server stopped successfully")

def load_config(config_path: str) -> Dict[str, Any]:
    """Load server configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json5.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found - using defaults")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid config file: {str(e)}")
        return {}

def main():
    """Main entry point with command-line argument support."""
    parser = argparse.ArgumentParser(description='Enhanced TCP Server for pytest-learn-multi-test-categories')
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