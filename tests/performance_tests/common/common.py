"""
Performance Test Common Utilities / 性能测试公共工具
"""
import time
import threading
import statistics
from typing import Dict, Any, List, Tuple
from client import Client


class PerformanceTestResult:
    """Performance test result container / 性能测试结果容器"""
    def __init__(self):
        self.test_name: str = ""
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.duration: float = 0.0
        self.response_times: List[float] = []
        self.throughput: float = 0.0  # requests per second
        self.errors: List[str] = []
        self.percentiles: Dict[str, float] = {}

    def calculate_metrics(self):
        """Calculate performance metrics / 计算性能指标"""
        if self.response_times:
            self.percentiles = {
                "p50": statistics.median(self.response_times),
                "p95": self.percentile(self.response_times, 95),
                "p99": self.percentile(self.response_times, 99),
                "min": min(self.response_times),
                "max": max(self.response_times),
                "avg": statistics.mean(self.response_times)
            }

        if self.duration > 0:
            self.throughput = self.successful_requests / self.duration

    def percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile / 计算百分位"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * (percentile / 100))
        return sorted_data[index]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary / 转换为字典"""
        self.calculate_metrics()
        return {
            "test_name": self.test_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "duration": self.duration,
            "throughput": self.throughput,
            "response_times_percentiles": self.percentiles,
            "errors": self.errors
        }


def measure_latency(client: Client, request: Dict[str, Any], iterations: int = 100) -> PerformanceTestResult:
    """
    Measure request latency / 测量请求延迟

    Args:
        client: Client instance / 客户端实例
        request: Request to measure / 要测量的请求
        iterations: Number of iterations / 迭代次数

    Returns:
        Performance test result / 性能测试结果
    """
    result = PerformanceTestResult()
    result.test_name = f"latency_{request.get('command', 'unknown')}"

    start_time = time.time()

    for i in range(iterations):
        request['id'] = i + 1
        result.total_requests += 1

        iter_start = time.time()
        try:
            success = client.send(request)
            iter_end = time.time()

            if success:
                result.successful_requests += 1
                result.response_times.append(iter_end - iter_start)
            else:
                result.failed_requests += 1
                result.errors.append(f"Iteration {i+1}: Send failed")
        except Exception as e:
            result.failed_requests += 1
            result.errors.append(f"Iteration {i+1}: {str(e)}")

        time.sleep(0.01)  # Small delay between requests

    result.duration = time.time() - start_time
    return result


def measure_throughput(client: Client, request: Dict[str, Any], duration: int = 10, target_rps: int = 50) -> PerformanceTestResult:
    """
    Measure throughput / 测量吞吐量

    Args:
        client: Client instance / 客户端实例
        request: Request to measure / 要测量的请求
        duration: Test duration in seconds / 测试持续时间(秒)
        target_rps: Target requests per second / 目标每秒请求数

    Returns:
        Performance test result / 性能测试结果
    """
    result = PerformanceTestResult()
    result.test_name = f"throughput_{request.get('command', 'unknown')}"

    start_time = time.time()
    interval = 1.0 / target_rps
    request_id = 0

    while time.time() - start_time < duration:
        request['id'] = request_id + 1
        iter_start = time.time()

        try:
            success = client.send(request)
            iter_end = time.time()

            result.total_requests += 1
            if success:
                result.successful_requests += 1
                result.response_times.append(iter_end - iter_start)
            else:
                result.failed_requests += 1
                result.errors.append(f"Request {request_id}: Send failed")
        except Exception as e:
            result.failed_requests += 1
            result.errors.append(f"Request {request_id}: {str(e)}")

        request_id += 1
        elapsed = time.time() - iter_start
        if elapsed < interval:
            time.sleep(interval - elapsed)

    result.duration = time.time() - start_time
    return result


def concurrent_test(client_creator, num_clients: int, requests_per_client: int = 10) -> PerformanceTestResult:
    """
    Run concurrent test / 运行并发测试

    Args:
        client_creator: Function to create client / 创建客户端的函数
        num_clients: Number of concurrent clients / 并发客户端数量
        requests_per_client: Requests per client / 每个客户端的请求数

    Returns:
        Performance test result / 性能测试结果
    """
    result = PerformanceTestResult()
    result.test_name = f"concurrent_{num_clients}_clients"

    results_lock = threading.Lock()
    threads = []

    def worker():
        client = client_creator()
        for i in range(requests_per_client):
            request = {
                "type": "request",
                "command": "health_check",
                "id": i + 1,
                "token": client.token
            }

            iter_start = time.time()
            try:
                success = client.send(request)
                iter_end = time.time()

                with results_lock:
                    result.total_requests += 1
                    if success:
                        result.successful_requests += 1
                        result.response_times.append(iter_end - iter_start)
                    else:
                        result.failed_requests += 1
            except Exception as e:
                with results_lock:
                    result.failed_requests += 1
                    result.errors.append(str(e))
        client.close()

    start_time = time.time()

    for _ in range(num_clients):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    result.duration = time.time() - start_time
    return result


def stress_test(client: Client, max_requests: int = 1000, max_duration: int = 300) -> PerformanceTestResult:
    """
    Run stress test / 运行压力测试

    Args:
        client: Client instance / 客户端实例
        max_requests: Maximum number of requests / 最大请求数
        max_duration: Maximum duration in seconds / 最大持续时间(秒)

    Returns:
        Performance test result / 性能测试结果
    """
    result = PerformanceTestResult()
    result.test_name = "stress_test"

    start_time = time.time()
    request_id = 0

    while request_id < max_requests and time.time() - start_time < max_duration:
        request = {
            "type": "request",
            "command": "health_check",
            "id": request_id + 1,
            "token": client.token
        }

        iter_start = time.time()
        try:
            success = client.send(request)
            iter_end = time.time()

            result.total_requests += 1
            if success:
                result.successful_requests += 1
                result.response_times.append(iter_end - iter_start)
            else:
                result.failed_requests += 1
                result.errors.append(f"Request {request_id}: Send failed")
        except Exception as e:
            result.failed_requests += 1
            result.errors.append(f"Request {request_id}: {str(e)}")

        request_id += 1

    result.duration = time.time() - start_time
    return result


def run_performance_suite(client: Client) -> List[PerformanceTestResult]:
    """
    Run complete performance test suite / 运行完整性能测试套件

    Args:
        client: Client instance / 客户端实例

    Returns:
        List of test results / 测试结果列表
    """
    results = []

    # Latency tests
    commands = [
        {"type": "request", "command": "get_status", "token": client.token},
        {"type": "request", "command": "health_check", "token": client.token},
        {"type": "request", "command": "echo_with_timestamp", "text": "test", "token": client.token}
    ]

    for request in commands:
        result = measure_latency(client, request, iterations=50)
        results.append(result)
        time.sleep(1)

    # Throughput test
    request = {"type": "request", "command": "health_check", "token": client.token}
    result = measure_throughput(client, request, duration=10, target_rps=20)
    results.append(result)

    # Concurrent test (simple version)
    result = concurrent_test(
        lambda: Client(client.host, client.port, client.token),
        num_clients=3,
        requests_per_client=10
    )
    results.append(result)

    return results
