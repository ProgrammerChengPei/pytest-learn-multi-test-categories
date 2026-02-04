"""
Function Test Configuration / 功能测试配置
"""
import sys
from pathlib import Path

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def interface_test_passed(test_state):
    """
    Check if interface test passed before running function tests
    在运行功能测试前检查接口测试是否通过
    """
    return test_state.interface_test_passed


@pytest.fixture
def function_test_scenarios():
    """
    Function test scenarios / 功能测试场景
    """
    return {
        "connection_lifecycle": {
            "description": "Test connection lifecycle management / 测试连接生命周期管理",
            "steps": ["connect", "send", "receive", "disconnect"]
        },
        "message_sequence": {
            "description": "Test message sequencing / 测试消息顺序",
            "steps": ["send_multiple", "verify_order"]
        },
        "error_recovery": {
            "description": "Test error recovery / 测试错误恢复",
            "steps": ["simulate_error", "verify_recovery"]
        },
        "data_integrity": {
            "description": "Test data integrity / 测试数据完整性",
            "steps": ["send_data", "verify_integrity"]
        }
    }


@pytest.fixture
def test_data_sets():
    """
    Test data sets for function tests / 功能测试数据集
    """
    return {
        "text_messages": [
            "Hello World",
            "测试中文消息",
            "Special chars: !@#$%^&*()",
            "Very long message: " + "A" * 1000
        ],
        "numeric_data": [
            0,
            1,
            100,
            999999
        ],
        "json_objects": [
            {"key1": "value1", "key2": "value2"},
            {"nested": {"data": "structure"}},
            {"array": [1, 2, 3, 4, 5]}
        ]
    }
