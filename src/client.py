"""
Test Client - Optimized Version
"""
import json
import socket
import threading
import time
from typing import Optional

from log import load_config, logger


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
        self.timeout = config.get('client_timeout', 10.0)
        
        self._connect()

    def _connect(self):
        """建立连接"""
        with self.lock:
            if self.connected:
                return True
                
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.timeout)  # 连接超时
                self.socket.connect((self.host, self.port))
                self.connected = True
                self.reconnect_attempts = 0
                
                # 启动响应处理线程
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
        """清理资源"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None

    def _handle_responses(self):
        """处理服务器响应"""
        while self.connected and self.socket:
            try:
                data = self.socket.recv(1024)
                
                if not data:
                    logger.info("Server closed connection")
                    break
                    
                response_str = data.decode('utf-8').strip()
                if response_str:
                    response = json.loads(response_str)
                    logger.info(f"Server response: {response}")
                    
                    # 处理断开命令
                    if response.get('command') == 'disconnect':
                        logger.info(f"Server requested disconnect: {response.get('reason', 'unknown')}")
                        break
                        
            except socket.timeout:
                continue  # 正常超时，继续循环
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response: {e}")
            except (ConnectionResetError, BrokenPipeError) as e:
                logger.info(f"Connection lost: {e}")
                break
            except Exception as e:
                logger.error(f"Error handling response: {e}")
                break
                
        # 连接断开
        with self.lock:
            self._cleanup()

    def send(self, request: dict) -> bool:
        """发送请求"""
        if not self.connected:
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                logger.error("Max reconnection attempts reached")
                return False
                
            self.reconnect_attempts += 1
            logger.info(f"Attempting to reconnect ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            
            if not self._connect():
                return False
        
        try:
            with self.lock:
                if not self.connected or not self.socket:
                    return False
                    
                message = json.dumps(request)
                self.socket.sendall(message.encode('utf-8'))
                logger.info(f"Sent request: {request}")
                return True
                
        except Exception as e:
            logger.error(f"Send failed: {e}")
            with self.lock:
                self._cleanup()
            return False

    def close(self):
        """关闭连接"""
        with self.lock:
            self._cleanup()

def send_requests(client: Client):
    """发送测试请求"""
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
            "text": f"Client message at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        },
        {
            "type": "request",
            "token": client.token,
            "command": "health_check",
            "id": 3
        }
    ]
    
    for i in range(2):  # 发送两轮
        logger.info(f"Sending request batch {i+1}")
        for request in requests:
            if client.send(request):
                time.sleep(0.5)  # 请求间隔
            else:
                logger.error("Failed to send request, stopping")
                return
                
        if i < 1:  # 第一轮后等待
            logger.info("Waiting before next batch...")
            time.sleep(15)

if __name__ == "__main__":
    try:
        config = load_config('configs/config.json')
        
        client = Client(
            config.get('host', 'localhost'),
            config.get('port', 8080),
            config.get('token', 'your-secure-token-here')
        )
        
        send_requests(client)
        
    except Exception as e:
        logger.error(f"Client error: {e}")
    finally:
        if 'client' in locals():
            client.close()
