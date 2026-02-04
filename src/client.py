"""
Test client for the enhanced TCP server.
Sends a valid request with correct message type and token.
"""
import json
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

from src.log import logger


class Client:
    def __init__(self, host: str, port: int, token: str):
        self.host = host
        self.port = port
        self.token = token
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.response_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 2  # Initial delay in seconds
        
        # Connect on initialization
        self._connect()

    def _connect(self) -> bool:
        """Establish connection to server."""
        with self.lock:
            if self.connected:
                return True
                
            try:
                # Clean up any existing socket
                if self.socket:
                    try:
                        self.socket.close()
                    except:
                        pass
                
                # Create new socket and connect
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(10.0)  # Connection timeout
                self.socket.connect((self.host, self.port))
                self.connected = True
                self.reconnect_attempts = 0
                
                # Start response handler thread
                self.response_thread = threading.Thread(
                    target=self._handle_responses, 
                    name="ResponseHandler",
                    daemon=True
                )
                self.response_thread.start()
                
                logger.info(f"Connected to {self.host}:{self.port}")
                return True
                
            except Exception as e:
                logger.error(f"Connection failed: {e}")
                self._cleanup()
                return False

    def _cleanup(self):
        """Clean up resources."""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None

    def _handle_responses(self):
        """Thread function to handle server responses."""
        buffer = b""
        while self.connected and self.socket:
            try:
                # Set receive timeout to allow checking connection status
                self.socket.settimeout(1.0)
                
                data = self.socket.recv(1024)
                if not data:
                    logger.info("Server closed connection")
                    break
                    
                buffer += data
                
                # Process complete messages (assuming newline-separated)
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if line:
                        self._process_response(line)
                        
            except socket.timeout:
                continue  # Normal timeout, continue loop
            except (ConnectionResetError, BrokenPipeError) as e:
                logger.info(f"Connection lost: {e}")
                break
            except OSError as e:
                # Socket errors (connection closed)
                logger.debug(f"Socket error in response handler: {e}")
                break
            except Exception as e:
                logger.error(f"Error handling response: {e}")
                break
                
        # Connection lost
        with self.lock:
            logger.info("Response handler exiting")
            self._cleanup()

    def _process_response(self, raw_data: bytes):
        """Process a single response from server."""
        try:
            response_str = raw_data.decode('utf-8').strip()
            if not response_str:
                return
                
            logger.info(f"Server response: {response_str}")
            
            # Parse JSON response
            try:
                message = json.loads(response_str)
                
                # Handle disconnect command
                if message.get('command') == "disconnect":
                    logger.info(f"Server requested disconnect: {message.get('reason', 'unknown')}")
                    with self.lock:
                        self._cleanup()
                    return
                    
            except json.JSONDecodeError:
                # Handle non-JSON responses
                if "timeout" in response_str.lower() or "disconnect" in response_str.lower():
                    logger.info(f"Server sent disconnect message: {response_str}")
                    with self.lock:
                        self._cleanup()
                else:
                    logger.warning(f"Non-JSON response: {response_str}")
                    
        except UnicodeDecodeError:
            logger.error(f"Failed to decode response: {raw_data}")
        except Exception as e:
            logger.error(f"Error processing response: {e}")

    def send(self, request: Dict[str, Any]) -> bool:
        """Send a request to the server."""
        # Reconnect if not connected
        if not self.connected:
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.error("Max reconnection attempts reached")
                return False
                
            self.reconnect_attempts += 1
            delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))  # Exponential backoff
            logger.info(f"Attempting to reconnect ({self.reconnect_attempts}/{self.max_reconnect_attempts}) in {delay}s")
            
            time.sleep(delay)
            if not self._connect():
                return False
        
        try:
            with self.lock:
                if not self.connected or not self.socket:
                    return False
                    
                # Add token to request if not present
                if 'token' not in request:
                    request['token'] = self.token
                    
                message = json.dumps(request) + '\n'  # Add newline for message separation
                self.socket.sendall(message.encode('utf-8'))
                logger.info(f"Sent request: {request}")
                return True
                
        except Exception as e:
            logger.error(f"Send failed: {e}")
            with self.lock:
                self._cleanup()
            return False

    def close(self):
        """Close the connection gracefully."""
        with self.lock:
            logger.info("Closing client connection")
            self._cleanup()

def send_requests(client: Client):
    """Function to send requests to the server."""
    # Create test requests
    dt = time.strftime("%Y-%m-%d %H:%M:%S")
    requests = [
        {
            "type": "request",
            "token": client.token,
            "command": "get_status",
            "id": 1
        },
        {
            "type": "request",
            "token": client.token,
            "command": "echo_with_timestamp",
            "id": 2,
            "text": f"Client message at {dt}",
            "client_timestamp": dt,
        },
        {
            "type": "request",
            "token": client.token,
            "command": "health_check",
            "id": 3
        },
    ]
    
    # Send requests in batches
    for batch_num in range(2):
        logger.info(f"Sending request batch {batch_num + 1}")
        
        for i, request in enumerate(requests):
            if not client.send(request):
                logger.error("Failed to send request, stopping")
                return
                
            # Small delay between requests
            if i < len(requests) - 1:
                time.sleep(0.2)
        
        # Wait between batches (shorter wait to avoid timeout)
        if batch_num < 1:
            logger.info("Waiting before next batch...")
            time.sleep(8)  # Shorter than server timeout

if __name__ == "__main__":
    try:
        # Load configuration
        config_path = 'configs/config.json'
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        host = config.get('host', 'localhost')
        port = config.get('port', 8080)
        token = config.get('token', 'your-secure-token-here')
        
        # Create client
        client = Client(host, port, token)
        
        # Send requests
        send_requests(client)
        
        # Keep the client running for a bit to receive responses
        time.sleep(2)
        
    except Exception as e:
        logger.error(f"Client error: {e}")
    finally:
        # Ensure client is closed
        if 'client' in locals():
            client.close()