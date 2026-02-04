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
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.total_requests: int = 0
        self.throughput: float = 0.0
        self.failed_requests: List[Dict[str, Any]] = []

    def add_response_time(self, response_time: float):
        """Add response time / 添加响应时间"""
        self.response_times.append(response_time)

    def add_success(self):
        """Increment successful request count / 增加成功请求计数"""
        self.successful_requests += 1
        self.total_requests += 1

    def add_failure(self, error: str = "", details: Dict[str, Any] = None):
        """Increment failed request count / 增加失败请求计数"""
        self.failed_requests += 1
        self.total_requests += 1
        if details:
            self.failed_requests.append({
                "error": error,
                "details": details,
                "timestamp": time.time()
            })

    def calculate_metrics(self):
        """Calculate performance metrics / 计算性能指标"""
        if self.total_requests > 0:
            self.throughput = self.total_requests / sum(self.response_times) if self.response_times else 0

    def get_statistics(self) -> Dict[str, float]:
        """Get statistics dictionary / 获取统计字典"""
        if not self.response_times:
            return {
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0
            }

        return {
            "avg": sum(self.response_times) / len(self.response_times),
            "min": min(self.response_times),
            "max": max(self.response_times),
            "count": len(self.response_times)
        }


def calculate_checksum(data: str) -> str:
    """
    Calculate MD5 checksum / 计算MD5校验和

    Args:
        data: Data to calculate checksum / 要计算校验和的数据

    Returns:
        MD5 checksum string / MD5校验和字符串
    """
    return hashlib.md5(data.encode('utf-8')).hexdigest()


def validate_timestamp(timestamp_str: str, tolerance_seconds: float = 60.0) -> bool:
    """
    Validate if timestamp is recent / 验证时间戳是否为最近时间

    Args:
        timestamp_str: Timestamp string / 时间戳字符串
        tolerance_seconds: Tolerance in seconds / 容差（秒）

    Returns:
        True if timestamp is recent / 如果时间戳是最近时间返回True
    """
    try:
        timestamp = float(timestamp_str)
        return abs(time.time() - timestamp) <= tolerance_seconds
    except (ValueError, TypeError):
        return False


def compare_timestamps(timestamp1: str, timestamp2: float, tolerance: float = 60.0) -> bool:
    """
    Compare two timestamps / 比较两个时间戳

    Args:
        timestamp1: First timestamp string / 第一个时间戳字符串
        timestamp2: Second timestamp as float / 第二个时间戳（浮点数）
        tolerance: Tolerance in seconds / 容差（秒）

    Returns:
        True if timestamps are close enough / 如果时间戳足够接近返回True
    """
    try:
        ts1 = float(timestamp1)
        return abs(ts1 - timestamp2) <= tolerance
    except (ValueError, TypeError):
        return False


# ============================================================================
# Test dependency decorators / 测试依赖装饰器
# ============================================================================

def require_flash_test(test_func):
    """
    装饰器：要求刷写测试通过 / Decorator: Require flash test to pass

    用法示例 / Usage example:
        @require_flash_test
        def test_something(test_state):
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
# Test phase marker decorators / 测试阶段标记装饰器
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
