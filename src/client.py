"""
Test client for the enhanced TCP server.
Sends a valid request with correct message type and token.
"""
import json
import logging
import socket
import threading
import time

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(thread)d - %(name)s %(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('log/client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Client:
    def __init__(self, host: str, port: int, token: str):
        self.host = host
        self.port = port
        self.token = token
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.connected = True
        self.response_thread = threading.Thread(target=self.handle_response)
        self.response_thread.start()

    def handle_response(self):
        while self.connected:
            try:
                raw = self.socket.recv(1024)
                if not raw:
                    # 连接已被关闭
                    self.connected = False
                    break

                response = raw.decode('utf-8')
                if not response.strip():  # 空响应
                    continue

                message = json.loads(response)
                logger.info(f"Server response: {response}")
                if message.get('command') == "disconnect":
                    self.connected = False
            except Exception as e:
                logger.error(f"Error handling response: {e}")

    def send(self, request):
        """Send a get_status request to the server and print the response."""
        # Correct message format with "type": "request"
        if not self.connected:
            logger.warning("Client is not connected")
            self.socket.close()
            logger.warning("Re-connect")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            # 必须创建新的线程对象，否则会报RuntimeError: threads can only be started once
            self.response_thread = threading.Thread(target=self.handle_response)
            self.response_thread.start()

        try:
            logger.info(f"Client request: {request}")
            self.socket.sendall(json.dumps(request).encode('utf-8'))
        except Exception as e:
            logger.error(f"Error sending request: {e}")


def send_request(client: Client):
    """Function to send a request to the server."""
    # todo: 创建响应服务器的线程
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
            "id": 1,
            "text": f"Client message at {dt}",
            "client_timestamp": dt,
        },
        {
            "type": "request",
            "token": client.token,
            "command": "health_check",
            "id": 1
        },
    ]
    for _ in range(2):
        for request in requests:
            client.send(request)
            time.sleep(0.2)
        time.sleep(10)

if __name__ == "__main__":
    config_path = 'configs/config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    host = config.get('host', 'localhost')
    port = config.get('port', 8080)
    token = config.get('token', "your-secure-token-here")
    client = Client(host, port, token)

    
    send_request(client)
    client.socket.close()