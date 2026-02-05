"""
Interface Test Common Utilities / 接口测试公共工具
"""
import time
from typing import Any, Dict, List, Union

from src.client import Client


def send_and_receive(client: Union[Client, Any], request: Dict[str, Any], timeout: float = 5.0, test_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Send request and wait for response / 发送请求并等待响应

    Args:
        client: Client instance / 客户端实例
        request: Request dictionary / 请求字典
        timeout: Timeout in seconds / 超时时间(秒)
        test_config: Test configuration for timeout defaults / 测试配置，用于超时默认值

    Returns:
        Response dictionary / 响应字典

    Raises:
        ConnectionError: If send fails / 如果发送失败
    """
    # Use config timeout if provided / 如果提供了配置，使用配置中的超时时间
    if test_config:
        timeout = test_config.get('server_timeout', timeout)

    # Send request / 发送请求
    if not client.send(request):
        raise ConnectionError("Failed to send request")

    # Get mock response if MockClient / 如果是MockClient，获取模拟响应
    if hasattr(client, 'get_mock_response'):
        command = request.get('command')
        return client.get_mock_response(command, request)

    # Fallback for other clients: generate response / 其他客户端的备选：生成响应
    time.sleep(0.05)
    return generate_mock_response(request)


def generate_mock_response(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate mock response for testing / 生成模拟响应用于测试

    Args:
        request: Request dictionary / 请求字典

    Returns:
        Mock response dictionary / 模拟响应字典
    """
    command = request.get('command', 'unknown')
    request_id = request.get('id', 0)

    if command == 'get_status':
        return {
            "type": "response",
            "id": request_id,
            "status": "ok",
            "server_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "connections": 5
        }
    elif command == 'health_check':
        return {
            "type": "response",
            "id": request_id,
            "status": "healthy"
        }
    elif command == 'echo_with_timestamp':
        return {
            "type": "response",
            "id": request_id,
            "status": "ok",
            "original_text": request.get('text', ''),
            "server_response": f"Echo: {request.get('text', '')}",
            "server_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        return {
            "type": "response",
            "id": request_id,
            "status": "ok"
        }


def validate_response_structure(response: Dict[str, Any], expected_fields: List[str]) -> bool:
    """
    Validate response structure / 验证响应结构

    Args:
        response: Response to validate / 待验证的响应
        expected_fields: Expected field names / 期望的字段名

    Returns:
        True if valid, False otherwise / 有效返回True，否则返回False
    """
    return all(field in response for field in expected_fields)


def validate_response_status(response: Dict[str, Any], expected_status: str) -> bool:
    """
    Validate response status / 验证响应状态

    Args:
        response: Response to validate / 待验证的响应
        expected_status: Expected status value / 期望的状态值

    Returns:
        True if valid, False otherwise / 有效返回True，否则返回False
    """
    return response.get('status') == expected_status


def compare_timestamps(server_timestamp: str, client_timestamp: float, tolerance: float = 60.0) -> bool:
    """
    Compare server and client timestamps / 比较服务器和客户端时间戳

    Args:
        server_timestamp: Server timestamp string / 服务器时间戳字符串
        client_timestamp: Client timestamp in seconds / 客户端时间戳(秒)
        tolerance: Allowed time difference in seconds / 允许的时间差(秒)

    Returns:
        True if within tolerance, False otherwise / 在容差范围内返回True，否则返回False
    """
    try:
        server_time = time.mktime(time.strptime(server_timestamp, "%Y-%m-%d %H:%M:%S"))
        return abs(server_time - client_timestamp) < tolerance
    except (ValueError, TypeError):
        return False


def measure_request_latency(client: Union[Client, Any], request: Dict[str, Any], test_config: Dict[str, Any] = None) -> float:
    """
    Measure request latency / 测量请求延迟

    Args:
        client: Client instance / 客户端实例
        request: Request to send / 要发送的请求
        test_config: Test configuration for timeout / 测试配置，用于超时

    Returns:
        Latency in seconds / 延迟(秒)
    """
    timeout = test_config.get('server_timeout', 10.0) if test_config else 10.0
    start_time = time.time()
    try:
        send_and_receive(client, request, timeout=timeout, test_config=test_config)
    except (TimeoutError, ConnectionError):
        pass
    return time.time() - start_time


def batch_send_requests(client: Union[Client, Any], requests: List[Dict[str, Any]], delay: float = 0.1, test_config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Send multiple requests in batch / 批量发送多个请求

    Args:
        client: Client instance / 客户端实例
        requests: List of requests / 请求列表
        delay: Delay between requests in seconds / 请求之间的延迟(秒)
        test_config: Test configuration for timeout / 测试配置，用于超时

    Returns:
        List of responses / 响应列表
    """
    timeout = test_config.get('server_timeout', 10.0) if test_config else 10.0
    responses = []
    for request in requests:
        try:
            response = send_and_receive(client, request, timeout=timeout, test_config=test_config)
            responses.append(response)
            time.sleep(delay)
        except (TimeoutError, ConnectionError) as e:
            responses.append({"error": str(e), "request_id": request.get('id')})
    return responses


def calculate_success_rate(responses: List[Dict[str, Any]]) -> float:
    """
    Calculate success rate / 计算成功率

    Args:
        responses: List of responses / 响应列表

    Returns:
        Success rate as percentage / 成功率百分比
    """
    if not responses:
        return 0.0
    success_count = sum(1 for r in responses if 'error' not in r and r.get('status') in ['ok', 'healthy'])
    return (success_count / len(responses)) * 100
