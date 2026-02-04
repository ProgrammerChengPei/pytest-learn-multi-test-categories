"""
Performance Test Configuration / 性能测试配置
"""
import sys
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))




@pytest.fixture(scope="session")
def function_test_passed(test_state):
    """
    Check if function test passed before running performance tests
    在运行性能测试前检查功能测试是否通过
    """
    return test_state.function_test_passed


@pytest.fixture
def performance_test_config():
    """
    Performance test configuration / 性能测试配置
    """
    return {
        "concurrent_connections": {
            "min": 1,
            "max": 10,
            "step": 2
        },
        "throughput": {
            "requests_per_second": [10, 50, 100, 200],
            "duration": 10  # seconds
        },
        "latency": {
            "target_p50": 0.1,  # seconds
            "target_p95": 0.5,
            "target_p99": 1.0
        },
        "stress": {
            "max_requests": 1000,
            "max_duration": 300  # seconds
        }
    }


@pytest.fixture
def performance_benchmarks():
    """
    Performance benchmarks / 性能基准
    """
    return {
        "get_status": {
            "max_latency": 0.2,
            "min_throughput": 10  # requests per second
        },
        "health_check": {
            "max_latency": 0.1,
            "min_throughput": 20
        },
        "echo_with_timestamp": {
            "max_latency": 0.3,
            "min_throughput": 15
        }
    }
