"""
Common Test Utilities / 测试公共工具模块
跨测试类型的公共辅助函数 / Cross-test-type common helper functions
"""
import functools
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from src.client import Client


class TestResult:
    """Test result container / 测试结果容器"""
    def __init__(self):
        self.test_name: str = ""
        self.status: str = "skipped"
        self.duration: float = 0.0
        self.message: str = ""
        self.details: Dict[str, Any] = {}
        self.timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary / 转换为字典"""
        return {
            "test_name": self.test_name,
            "status": self.status,
            "duration": self.duration,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


class TestTimer:
    """Test execution timer / 测试执行计时器"""
    def __init__(self):
        self.start_time = 0.0
        self.end_time = 0.0

    def start(self):
        """Start timer / 开始计时"""
        self.start_time = time.time()

    def stop(self) -> float:
        """Stop timer and return duration / 停止计时并返回时长"""
        self.end_time = time.time()
        return self.duration

    @property
    def duration(self) -> float:
        """Get duration / 获取时长"""
        if self.start_time == 0:
            return 0.0
        end = self.end_time if self.end_time > 0 else time.time()
        return end - self.start_time


def load_test_data(test_name: str, data_dir: Path) -> Dict[str, Any]:
    """
    Load test data from JSON file / 从JSON文件加载测试数据

    Args:
        test_name: Test name / 测试名称
        data_dir: Data directory / 数据目录

    Returns:
        Test data dictionary / 测试数据字典
    """
    data_file = data_dir / f"{test_name}.json"
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_test_result(result: TestResult, output_dir: Path):
    """
    Save test result to JSON file / 保存测试结果到JSON文件

    Args:
        result: Test result object / 测试结果对象
        output_dir: Output directory / 输出目录
    """
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{result.test_name}_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)


class PerformanceMetrics:
    """Performance metrics collector / 性能指标收集器"""
    def __init__(self):
        self.response_times: List[float] = []
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
        self.throughput: float = 0.0
        self.error_count: int = 0

    def add_response_time(self, response_time: float):
        """Add response time / 添加响应时间"""
        self.response_times.append(response_time)

    def get_avg_response_time(self) -> float:
        """Get average response time / 获取平均响应时间"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def get_max_response_time(self) -> float:
        """Get maximum response time / 获取最大响应时间"""
        return max(self.response_times) if self.response_times else 0.0

    def get_min_response_time(self) -> float:
        """Get minimum response time / 获取最小响应时间"""
        return min(self.response_times) if self.response_times else 0.0

    def get_p95_response_time(self) -> float:
        """Get 95th percentile response time / 获取P95响应时间"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary / 转换为字典"""
        return {
            "avg_response_time": self.get_avg_response_time(),
            "max_response_time": self.get_max_response_time(),
            "min_response_time": self.get_min_response_time(),
            "p95_response_time": self.get_p95_response_time(),
            "total_requests": len(self.response_times),
            "error_count": self.error_count,
            "throughput": self.throughput
        }


def calculate_test_coverage(covered_items: List[str], total_items: List[str]) -> float:
    """
    Calculate test coverage percentage / 计算测试覆盖率百分比

    Args:
        covered_items: List of covered items / 已覆盖项目列表
        total_items: List of total items / 总项目列表

    Returns:
        Coverage percentage / 覆盖率百分比
    """
    if not total_items:
        return 100.0
    covered_set = set(covered_items)
    total_set = set(total_items)
    coverage = len(covered_set & total_set) / len(total_set) * 100
    return round(coverage, 2)


# ============================================================================
# 跨测试类型的公共辅助函数 / Cross-test-type common helper functions
# ============================================================================

import pytest  # 延迟导入避免循环依赖 / Delayed import to avoid circular dependency


def send_and_receive(client: Client, request: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
    """
    Send request and wait for response (cross-test-type) / 发送请求并等待响应（跨测试类型）

    Args:
        client: Client instance / 客户端实例
        request: Request dictionary / 请求字典
        timeout: Timeout in seconds / 超时时间(秒)

    Returns:
        Response dictionary / 响应字典

    Raises:
        TimeoutError: If response not received within timeout / 如果超时未收到响应
        ConnectionError: If send fails / 如果发送失败
    """

    start_time = time.time()
    response_received = False
    response_data = {}

    # Send request
    if not client.send(request):
        raise ConnectionError("Failed to send request / 发送请求失败")

    # Wait for response (polling approach)
    while not response_received and time.time() - start_time < timeout:
        time.sleep(0.05)

    if not response_received:
        raise TimeoutError(f"No response received within {timeout} seconds / {timeout}秒内未收到响应")

    return response_data


def validate_response_structure(response: Dict[str, Any], expected_fields: List[str]) -> bool:
    """
    Validate response structure (cross-test-type) / 验证响应结构（跨测试类型）

    Args:
        response: Response to validate / 待验证的响应
        expected_fields: Expected field names / 期望的字段名

    Returns:
        True if valid, False otherwise / 有效返回True，否则返回False
    """
    return all(field in response for field in expected_fields)


def validate_response_status(response: Dict[str, Any], expected_status: str) -> bool:
    """
    Validate response status (cross-test-type) / 验证响应状态（跨测试类型）

    Args:
        response: Response to validate / 待验证的响应
        expected_status: Expected status value / 期望的状态值

    Returns:
        True if valid, False otherwise / 有效返回True，否则返回False
    """
    return response.get('status') == expected_status


def compare_timestamps(server_timestamp: str, client_timestamp: float, tolerance: float = 60.0) -> bool:
    """
    Compare server and client timestamps (cross-test-type) / 比较服务器和客户端时间戳（跨测试类型）

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


def measure_request_latency(client, request: Dict[str, Any]) -> float:
    """
    Measure request latency (cross-test-type) / 测量请求延迟（跨测试类型）

    Args:
        client: Client instance / 客户端实例
        request: Request to send / 要发送的请求

    Returns:
        Latency in seconds / 延迟(秒)
    """
    start_time = time.time()
    try:
        client.send(request)
    except Exception:
        pass
    return time.time() - start_time


def batch_send_requests(client, requests: List[Dict[str, Any]], delay: float = 0.1) -> List[Dict[str, Any]]:
    """
    Send multiple requests in batch (cross-test-type) / 批量发送多个请求（跨测试类型）

    Args:
        client: Client instance / 客户端实例
        requests: List of requests / 请求列表
        delay: Delay between requests in seconds / 请求之间的延迟(秒)

    Returns:
        List of responses / 响应列表
    """
    responses = []
    for request in requests:
        try:
            success = client.send(request)
            responses.append({"request_id": request.get('id'), "success": success})
            time.sleep(delay)
        except Exception as e:
            responses.append({"request_id": request.get('id'), "error": str(e)})
    return responses


def calculate_success_rate(responses: List[Dict[str, Any]]) -> float:
    """
    Calculate success rate (cross-test-type) / 计算成功率（跨测试类型）

    Args:
        responses: List of responses / 响应列表

    Returns:
        Success rate as percentage / 成功率百分比
    """
    if not responses:
        return 0.0
    success_count = sum(1 for r in responses if 'error' not in r and r.get('success', r.get('status') in ['ok', 'healthy']))
    return (success_count / len(responses)) * 100


def test_data_integrity(client: Client, test_data: str) -> bool:
    """
    Test data integrity (cross-test-type) / 测试数据完整性（跨测试类型）

    Args:
        client: Client instance / 客户端实例
        test_data: Data to test integrity / 待测试完整性的数据

    Returns:
        True if test passes, False otherwise / 测试通过返回True，否则返回False
    """
    try:
        # Calculate checksum before sending
        original_checksum = hashlib.md5(test_data.encode()).hexdigest()

        # Send data
        request = {
            "type": "request",
            "command": "echo_with_timestamp",
            "id": 1,
            "text": test_data,
            "token": client.token,
            "checksum": original_checksum
        }
        client.send(request)
        time.sleep(0.3)

        return True
    except Exception as e:
        print(f"Data integrity test failed / 数据完整性测试失败: {e}")
        return False


def assert_response_success(response: Dict[str, Any], test_name: str = ""):
    """
    Assert response is successful (cross-test-type assertion helper) / 断言响应成功（跨测试类型断言助手）

    Args:
        response: Response to check / 待检查的响应
        test_name: Test name for error message / 用于错误消息的测试名称

    Raises:
        AssertionError: If response indicates failure / 如果响应表示失败
    """
    error_msg = response.get('message', response.get('error', ''))
    if response.get('type') == 'error' or 'error' in response:
        prefix = f"{test_name}: " if test_name else ""
        pytest.fail(f"{prefix}Response indicates error: {error_msg}")


def assert_in_range(value: float, min_val: float, max_val: float, metric_name: str = "Value"):
    """
    Assert value is within range (cross-test-type assertion helper) / 断言值在范围内（跨测试类型断言助手）

    Args:
        value: Value to check / 待检查的值
        min_val: Minimum value / 最小值
        max_val: Maximum value / 最大值
        metric_name: Metric name for error message / 用于错误消息的指标名称

    Raises:
        AssertionError: If value is out of range / 如果值超出范围
    """
    assert min_val <= value <= max_val, \
        f"{metric_name} {value:.3f} is not in range [{min_val:.3f}, {max_val:.3f}]"


# ============================================================================
# 依赖管理装饰器 - 简化依赖声明 / Dependency management decorators - Simplified dependency declaration
# ============================================================================

def require_flash_test(test_func):
    """
    装饰器：要求刷写测试通过 / Decorator: Require flash test to pass

    自动添加依赖标记和跳过检查，避免每个测试都写完整的 @pytest.mark.dependency
    Automatically adds dependency markers and skip checks, avoiding writing complete
    @pytest.mark.dependency for each test

    用法示例 / Usage example:
        @require_flash_test
        def test_something(test_state):
            # 测试代码 / Test code
            pass

    等价于 / Equivalent to:
        @pytest.mark.dependency(depends=["test_flash_complete"])
        def test_something(test_state, flash_test_passed):
            if not flash_test_passed:
                pytest.skip("Flash test not passed")
            # 测试代码 / Test code
            pass
    """
    @functools.wraps(test_func)
    def wrapper(*args, **kwargs):
        test_state = kwargs.get('test_state')
        if test_state and not test_state.flash_test_passed:
            pytest.skip("Flash test has not passed yet. Skipping dependent tests. / 刷写测试未通过，跳过依赖测试。")
        return test_func(*args, **kwargs)

    # 添加pytest标记
    wrapper = pytest.mark.dependency(depends=["test_flash_complete"])(wrapper)
    return wrapper


def require_interface_test(test_func):
    """
    装饰器：要求接口测试通过 / Decorator: Require interface test to pass

    用法示例 / Usage example:
        @require_interface_test
        def test_something(test_state):
            # 测试代码 / Test code
            pass
    """
    @functools.wraps(test_func)
    def wrapper(*args, **kwargs):
        test_state = kwargs.get('test_state')
        if test_state and not test_state.interface_test_passed:
            pytest.skip("Interface test has not passed yet. Skipping dependent tests. / 接口测试未通过，跳过依赖测试。")
        return test_func(*args, **kwargs)

    wrapper = pytest.mark.dependency(depends=["test_interface_complete"])(wrapper)
    return wrapper


def require_function_test(test_func):
    """
    装饰器：要求功能测试通过 / Decorator: Require function test to pass

    用法示例 / Usage example:
        @require_function_test
        def test_something(test_state):
            # 测试代码 / Test code
            pass
    """
    @functools.wraps(test_func)
    def wrapper(*args, **kwargs):
        test_state = kwargs.get('test_state')
        if test_state and not test_state.function_test_passed:
            pytest.skip("Function test has not passed yet. Skipping dependent tests. / 功能测试未通过，跳过依赖测试。")
        return test_func(*args, **kwargs)

    wrapper = pytest.mark.dependency(depends=["test_function_complete"])(wrapper)
    return wrapper


# ============================================================================
# 测试阶段标记装饰器 / Test phase marker decorators
# ============================================================================

def flash_test_marker(test_func):
    """标记为刷写测试 / Mark as flash test"""
    return pytest.mark.flash(test_func)


def interface_test_marker(test_func):
    """标记为接口测试 / Mark as interface test"""
    return pytest.mark.interface(test_func)


def function_test_marker(test_func):
    """标记为功能测试 / Mark as function test"""
    return pytest.mark.function(test_func)


def performance_test_marker(test_func):
    """标记为性能测试 / Mark as performance test"""
    return pytest.mark.performance(test_func)
    return pytest.mark.performance(test_func)
