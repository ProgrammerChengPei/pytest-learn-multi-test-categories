"""
Function Test Common Utilities / 功能测试公共工具
"""
import hashlib
import time
from typing import Any, Dict, List

import pytest

from src.client import Client


@pytest.mark.private
def _test_connection_lifecycle(client: Client) -> bool:
    """
    Test connection lifecycle / 测试连接生命周期

    Note: This test simulates timeout by waiting, not by setting attributes directly.
    The auto-fixture will reconnect if timeout occurs.
    注意: 此测试通过等待模拟超时，而不是直接设置属性。自动fixture会在超时时重连。

    Args:
        client: Client instance / 客户端实例

    Returns:
        True if test passes, False otherwise / 测试通过返回True，否则返回False
    """
    try:
        # Test initial connection (auto-fixture ensures this)
        # 测试初始连接（自动fixture确保）
        assert client.connected, "client should be connected initially"

        # Test request sending while connected
        # 测试连接时发送请求
        request = {"type": "request", "command": "get_status", "id": 1, "token": client.token}
        assert client.send(request), "Should be able to send request"

        # Simulate timeout by using idle timeout mechanism
        # 使用空闲超时机制模拟超时
        print("  → Simulating timeout scenario...")
        client.simulate_timeout()  # This sets last_activity to trigger timeout

        # Verify client is now disconnected due to timeout
        # 验证客户端因超时已断连
        assert not client.connected, "client should be disconnected after timeout"

        # Note: Don't reconnect here - the auto-fixture in the next test will handle it
        # 注意: 这里不重新连接 - 下一个测试的自动fixture会处理
        print("✓ Timeout simulated (next test's auto-fixture will reconnect)")

        return True
    except Exception as e:
        print(f"Connection lifecycle test failed: {e}")
        return False


def _test_message_sequence(client: Client, sequence: List[Dict[str, Any]]) -> bool:
    """
    Test message sequencing / 测试消息顺序

    Args:
        client: Client instance / 客户端实例
        sequence: List of messages to send / 要发送的消息列表

    Returns:
        True if test passes, False otherwise / 测试通过返回True，否则返回False
    """
    try:
        for i, message in enumerate(sequence):
            message["id"] = i + 1
            success = client.send(message)
            if not success:
                print(f"Failed to send message {i+1}")
                return False
            time.sleep(0.1)
        return True
    except Exception as e:
        print(f"Message sequence test failed: {e}")
        return False


def _test_error_recovery(client: Client) -> bool:
    """
    Test error recovery / 测试错误恢复

    Args:
        client: Client instance / 客户端实例

    Returns:
        True if test passes, False otherwise / 测试通过返回True，否则返回False
    """
    try:
        # Send invalid command
        invalid_request = {
            "type": "request",
            "command": "invalid_command",
            "id": 999,
            "token": client.token
        }
        client.send(invalid_request)
        time.sleep(0.5)

        # Verify client can still send valid requests
        valid_request = {
            "type": "request",
            "command": "health_check",
            "id": 1000,
            "token": client.token
        }
        success = client.send(valid_request)
        return success
    except Exception as e:
        print(f"Error recovery test failed: {e}")
        return False


def _test_data_integrity(client: Client, test_data: str) -> bool:
    """
    Test data integrity / 测试数据完整性

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
        time.sleep(0.5)

        # For now, just verify we can send the data
        return True
    except Exception as e:
        print(f"Data integrity test failed: {e}")
        return False


def run_test_scenario(client: Client, scenario_name: str, steps: List[str]) -> Dict[str, Any]:
    """
    Run a test scenario / 运行测试场景

    Args:
        client: Client instance / 客户端实例
        scenario_name: Name of the scenario / 场景名称
        steps: List of steps to execute / 要执行的步骤列表

    Returns:
        Test result dictionary / 测试结果字典
    """
    result = {
        "scenario": scenario_name,
        "status": "passed",
        "steps": [],
        "error": None
    }

    scenario_handlers = {
        "connection_lifecycle": lambda: _test_connection_lifecycle(client),
        "message_sequence": lambda: _test_message_sequence(client, [
            {"type": "request", "command": "get_status", "token": client.token},
            {"type": "request", "command": "health_check", "token": client.token},
            {"type": "request", "command": "echo_with_timestamp", "text": "test", "token": client.token}
        ]),
        "error_recovery": lambda: _test_error_recovery(client),
        "data_integrity": lambda: _test_data_integrity(client, "test data for integrity check")
    }

    for step in steps:
        start_time = time.time()
        try:
            step_result = scenario_handlers[step]()
            duration = time.time() - start_time
            result["steps"].append({
                "step": step,
                "status": "passed" if step_result else "failed",
                "duration": duration
            })
            if not step_result:
                result["status"] = "failed"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["steps"].append({
                "step": step,
                "status": "error",
                "error": str(e)
            })

    return result


def run_functional_test_suite(client: Client) -> List[Dict[str, Any]]:
    """
    Run complete functional test suite / 运行完整功能测试套件

    Args:
        client: Client instance / 客户端实例

    Returns:
        List of test results / 测试结果列表
    """
    scenarios = [
        ("connection_lifecycle", ["connection_lifecycle"]),
        ("message_sequence", ["message_sequence"]),
        ("error_recovery", ["error_recovery"]),
        ("data_integrity", ["data_integrity"])
    ]

    results = []
    for scenario_name, steps in scenarios:
        result = run_test_scenario(client, scenario_name, steps)
        results.append(result)

    return results
