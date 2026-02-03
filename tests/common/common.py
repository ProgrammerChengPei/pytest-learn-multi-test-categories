"""
Common Test Utilities / 测试公共工具模块
跨测试类型的公共辅助函数 / Cross-test-type common helper functions
"""
import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import functools


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
