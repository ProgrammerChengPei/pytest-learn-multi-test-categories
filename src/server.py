"""
Enhanced TCP Server - Optimized Version
"""
import argparse
import json
import os
import socket
import threading
import time
from typing import Any, Dict, Optional

from log import load_config, logger


class ConnectionManager:
    """管理客户端连接状态"""
    def __init__(self, heartbeat_interval: int = 30):
        self.heartbeat_interval = heartbeat_interval
        self.active_connections: Dict[socket.socket, Dict[str, Any]] = {}
        self.lock = threading.Lock()
    
    def add_connection(self, sock: socket.socket):
        """添加新连接"""
        with self.lock:
            self.active_connections[sock] = {
                'last_active': time.time(),
                'address': sock.getpeername()
            }
    
    def update_activity(self, sock: socket.socket):
        """更新连接活动时间"""
        with self.lock:
            if sock in self.active_connections:
                self.active_connections[sock]['last_active'] = time.time()
    
    def get_timeout_connections(self) -> list:
        """获取超时连接"""
        current_time = time.time()
        timeout_connections = []
        
        with self.lock:
            for sock, info in list(self.active_connections.items()):
                if current_time - info['last_active'] > self.heartbeat_interval:
                    timeout_connections.append(sock)
        
        return timeout_connections
    
    def remove_connection(self, sock: socket.socket):
        """移除连接"""
        with self.lock:
            if sock in self.active_connections:
                del self.active_connections[sock]
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        with self.lock:
            return len(self.active_connections)

class SimpleTCPServer:
    def __init__(self, config: Dict[str, Any]):
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8080)
        self.max_connections = config.get('max_connections', 100)
        self.heartbeat_interval = config.get('heartbeat_interval', 30)
        self.token = config.get('token', '')
        self.timeout = config.get('server_timeout', 10.0)
        self.client_timeout = config.get('client_timeout', 10.0)
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.running = False
        self.connection_manager = ConnectionManager(self.heartbeat_interval)
        self.heartbeat_thread: Optional[threading.Thread] = None

    def handle_client(self, client_socket: socket.socket):
        """处理客户端连接"""
        client_addr = client_socket.getpeername()
        logger.info(f"Client connected: {client_addr}")
        
        try:
            # 设置socket超时
            client_socket.settimeout(self.client_timeout)
            
            while self.running and client_socket in self.connection_manager.active_connections.keys():
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break  # 客户端主动关闭连接
                    
                    # 更新活动时间
                    self.connection_manager.update_activity(client_socket)
                    
                    message_str = data.decode('utf-8').strip()
                    if not message_str:
                        continue
                    
                    response = self._process_message(client_addr, message_str)
                    if response:
                        client_socket.sendall(json.dumps(response).encode('utf-8'))
                        
                except socket.timeout:
                    # 超时继续循环，检查服务器运行状态
                    continue
                except (ConnectionResetError, BrokenPipeError):
                    logger.info(f"Client {client_addr} disconnected unexpectedly")
                    break
                    
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {str(e)}")
        finally:
            self._cleanup_connection(client_socket, client_addr)

    def _process_message(self, client_addr: tuple, message_str: str) -> Optional[Dict[str, Any]]:
        """处理客户端消息"""
        try:
            message = json.loads(message_str)
            logger.info(f"Received from {client_addr}: {message}")
            
            # 认证检查
            if self.token and message.get('token') != self.token:
                return {"type": "error", "message": "Unauthorized"}
            
            message_type = message.get('type')
            if message_type == 'request':
                return self._handle_request(message)
            elif message_type == 'heartbeat':
                return {"type": "heartbeat_ack"}
            else:
                return {"type": "error", "message": f"Unknown message type: {message_type}"}
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {client_addr}: {e}")
            return {"type": "error", "message": "Invalid JSON format"}
        except Exception as e:
            logger.error(f"Error processing message from {client_addr}: {e}")
            return {"type": "error", "message": "Internal server error"}

    def _handle_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求消息"""
        command = message.get('command')
        request_id = message.get('id', 1)
        
        handlers = {
            'get_status': self._handle_get_status,
            'health_check': self._handle_health_check,
            'echo_with_timestamp': self._handle_echo_timestamp
        }
        
        handler = handlers.get(command)
        if handler:
            return handler(message, request_id)
        else:
            return {"type": "error", "id": request_id, "message": f"Unknown command: {command}"}

    def _handle_get_status(self, message: Dict[str, Any], request_id: int) -> Dict[str, Any]:
        return {
            "type": "response", 
            "id": request_id, 
            "status": "ok", 
            "server_time": time.time(),
            "connections": self.connection_manager.get_connection_count()
        }

    def _handle_health_check(self, message: Dict[str, Any], request_id: int) -> Dict[str, Any]:
        return {"type": "response", "id": request_id, "status": "healthy"}

    def _handle_echo_timestamp(self, message: Dict[str, Any], request_id: int) -> Dict[str, Any]:
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

    def _cleanup_connection(self, client_socket: socket.socket, client_addr: tuple):
        """清理连接资源"""
        try:
            self.connection_manager.remove_connection(client_socket)
            client_socket.close()
            logger.info(f"Connection closed: {client_addr}")
        except Exception as e:
            logger.error(f"Error cleaning up connection {client_addr}: {e}")

    def _start_heartbeat_monitor(self):
        """启动心跳监控"""
        def monitor():
            while self.running:
                try:
                    timeout_connections = self.connection_manager.get_timeout_connections()
                    for sock in timeout_connections:
                        try:
                            logger.warning(f"Connection timeout: {sock.getpeername()}")
                            # 发送断开通知
                            disconnect_msg = {"type": "response", "command": "disconnect", "reason": "timeout"}
                            sock.sendall(json.dumps(disconnect_msg).encode('utf-8'))
                            self._cleanup_connection(sock, sock.getpeername())
                        except Exception as e:
                            logger.error(f"Error handling timeout connection: {e}")
                            self.connection_manager.remove_connection(sock)
                    
                    time.sleep(self.heartbeat_interval)  # 每10秒检查一次
                except Exception as e:
                    logger.error(f"Heartbeat monitor error: {e}")
                    time.sleep(self.heartbeat_interval)
        
        self.heartbeat_thread = threading.Thread(target=monitor, name="HeartbeatMonitor", daemon=True)
        self.heartbeat_thread.start()

    def start(self):
        """启动服务器"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_connections)
            self.server_socket.settimeout(self.timeout)  # 设置accept超时
            self.running = True
            
            self._start_heartbeat_monitor()
            
            logger.info(f"Server started on {self.host}:{self.port} "
                       f"(max_connections: {self.max_connections}, "
                       f"heartbeat: {self.heartbeat_interval}s)")
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    
                    # 检查连接限制
                    if self.connection_manager.get_connection_count() >= self.max_connections:
                        logger.warning(f"Rejecting connection from {addr}: max connections reached")
                        client_socket.sendall(json.dumps({
                            "type": "error", 
                            "message": "Server busy"
                        }).encode('utf-8'))
                        client_socket.close()
                        continue
                    
                    self.connection_manager.add_connection(client_socket)
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket,),
                        name=f"ClientHandler-{addr[1]}",
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue  # 正常超时，继续循环
                    
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.stop()

    def stop(self):
        """停止服务器"""
        if not self.running:
            return
            
        logger.info("Stopping server...")
        self.running = False
        
        # 关闭所有客户端连接
        for sock in list(self.connection_manager.active_connections.keys()):
            try:
                sock.close()
            except Exception as e:
                logger.error(f"Error closing client socket: {e}")
        
        # 关闭服务器socket
        try:
            self.server_socket.close()
        except Exception as e:
            logger.error(f"Error closing server socket: {e}")
        
        logger.info("Server stopped")


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