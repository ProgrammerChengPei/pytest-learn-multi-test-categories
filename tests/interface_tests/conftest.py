"""
Interface Test Configuration / 接口测试配置
"""
import sys
import time
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))




@pytest.fixture(scope="session")
def flash_test_passed(test_state):
    """
    Check if flash test passed before running interface tests
    在运行接口测试前检查刷写测试是否通过
    """
    return test_state.flash_test_passed



@pytest.fixture
def mock_flash_data():
    """
    Mock flash test data for testing / 模拟刷写测试数据
    """
    return {
        "flash_success": True,
        "flash_version": "1.0.0",
        "flash_size": 1024000,
        "flash_checksum": "abc123",
        "flash_timestamp": time.time()
    }


@pytest.fixture
def interface_test_data():
    """
    Interface test data / 接口测试数据
    """
    return {
        "get_status": {
            "expected_fields": ["type", "id", "status", "server_time", "connections"],
            "expected_status": "ok"
        },
        "health_check": {
            "expected_fields": ["type", "id", "status"],
            "expected_status": "healthy"
        },
        "echo_with_timestamp": {
            "expected_fields": ["type", "id", "status", "original_text", "server_response", "server_timestamp"],
            "expected_status": "ok"
        }
    }


@pytest.fixture
def interface_requests():
    """
    Predefined interface requests / 预定义接口请求
    """
    return {
        "get_status": {
            "type": "request",
            "command": "get_status",
            "id": 1
        },
        "health_check": {
            "type": "request",
            "command": "health_check",
            "id": 2
        },
        "echo_with_timestamp": {
            "type": "request",
            "command": "echo_with_timestamp",
            "id": 3,
            "text": "Test message"
        }
    }
