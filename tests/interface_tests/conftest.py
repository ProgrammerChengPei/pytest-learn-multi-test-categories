"""
Interface Test Configuration / 接口测试配置
"""
import pytest
import json
import time
from typing import Dict, Any
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from client import Client


@pytest.fixture(scope="session")
def flash_test_passed(test_state):
    """
    Check if flash test passed before running interface tests
    在运行接口测试前检查刷写测试是否通过
    """
    return test_state.flash_test_passed


@pytest.fixture(scope="session")
def test_client(test_config):
    """
    Create test client instance / 创建测试客户端实例

    Note: This fixture will only be valid if flash test has passed
    注意: 仅在刷写测试通过后此fixture才有效
    """
    client = Client(
        test_config.get('host', 'localhost'),
        test_config.get('port', 8080),
        test_config.get('token', 'your-secure-token-here')
    )
    yield client
    client.close()


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
