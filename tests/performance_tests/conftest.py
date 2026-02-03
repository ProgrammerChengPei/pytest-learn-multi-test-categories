"""
Performance Test Configuration / 性能测试配置
"""
import pytest
import time
from typing import Dict, Any
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from client import Client


@pytest.fixture(scope="session")
def function_test_passed(test_state):
    """
    Check if function test passed before running performance tests
    在运行性能测试前检查功能测试是否通过
    """
    return test_state.function_test_passed


@pytest.fixture(scope="session")
def test_client(test_config):
    """
    Create test client instance for performance tests / 为性能测试创建测试客户端实例

    Note: Requires flash, interface, and function tests to pass
    注意: 需要刷写、接口和功能测试都通过
    """
    client = Client(
        test_config.get('host', 'localhost'),
        test_config.get('port', 8080),
        test_config.get('token', 'your-secure-token-here')
    )
    yield client
    client.close()


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
