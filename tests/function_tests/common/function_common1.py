"""
Function Test Common Utilities / 功能测试公共工具
"""
import hashlib
import time
from typing import Any, Dict, List

import pytest

from src.client import Client


@pytest.mark.private
def _test_connection_lifecycle(client: Client) -> None:
    """
    Test connection lifecycle / 测试连接生命周期

    Note: Uses simulate_timeout() method to simulate idle timeout.
    Exception is not caught so pytest and Allure can report detailed failure info.
    注意: 使用 simulate_timeout() 方法模拟空闲超时。
    不捕获异常，以便 pytest 和 Allure 能报告详细的失败信息。

    Args:
        client: Client instance / 客户端实例

    Raises:
        AssertionError: If any assertion fails / 如果任何断言失败则抛出
    """
    # Test initial connection
    assert client.connected, "Client should be connected initially"

    # Test request sending while connected
    request = {"type": "request", "command": "get_status", "id": 1, "token": client.token}
    assert client.send(request), "Should be able to send request"

    # Simulate timeout
    print("  → Simulating idle timeout scenario...")
    client.simulate_timeout()

    # Verify disconnection
    assert not client._connected, "Client should be disconnected after timeout"

    # Reconnect for next test
    client.reconnect()
    print("  ✓ Connection lifecycle test passed")


@pytest.mark.private
def _test_message_sequence(client: Client, sequence: List[Dict[str, Any]]) -> None:
    """
    Test message sequencing / 测试消息顺序

    Note: Exception is not caught so pytest and Allure can report detailed failure info.
    注意: 不捕获异常，以便 pytest 和 Allure 能报告详细的失败信息。

    Args:
        client: Client instance / 客户端实例
        sequence: List of messages to send / 要发送的消息列表

    Raises:
        AssertionError: If any assertion fails / 如果任何断言失败则抛出
    """
    for i, message in enumerate(sequence):
        message["id"] = i + 1
        success = client.send(message)
        assert success, f"Failed to send message {i+1}"
        time.sleep(0.05)

    print(f"  ✓ Message sequence test passed ({len(sequence)} messages)")


@pytest.mark.private
def _test_error_recovery(client: Client) -> None:
    """
    Test error recovery / 测试错误恢复

    Note: Exception is not caught so pytest and Allure can report detailed failure info.
    注意: 不捕获异常，以便 pytest 和 Allure 能报告详细的失败信息。

    Args:
        client: Client instance / 客户端实例

    Raises:
        AssertionError: If any assertion fails / 如果任何断言失败则抛出
    """
    # Send invalid command
    invalid_request = {
        "type": "request",
        "command": "invalid_command",
        "id": 999,
        "token": client.token
    }
    client.send(invalid_request)
    time.sleep(0.1)

    # Verify client can still send valid requests
    valid_request = {
        "type": "request",
        "command": "health_check",
        "id": 1000,
        "token": client.token
    }
    success = client.send(valid_request)
    assert success, "Should be able to send valid request after error"

    print("  ✓ Error recovery test passed")


@pytest.mark.private
def _test_data_integrity(client: Client, test_data: str) -> None:
    """
    Test data integrity / 测试数据完整性

    Note: Exception is not caught so pytest and Allure can report detailed failure info.
    注意: 不捕获异常，以便 pytest 和 Allure 能报告详细的失败信息。

    Args:
        client: Client instance / 客户端实例
        test_data: Data to test integrity / 待测试完整性的数据

    Raises:
        AssertionError: If any assertion fails / 如果任何断言失败则抛出
    """
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
    success = client.send(request)
    assert success, "Should be able to send data with integrity check"
    time.sleep(0.1)

    print("  ✓ Data integrity test passed")


def run_test_scenario(client: Client, scenario_name: str, steps: List[str]) -> Dict[str, Any]:
    """
    Run a test scenario / 运行测试场景

    Note: This function is used for programmatic execution.
    Exceptions are caught to return result dictionary.
    注意: 此函数用于程序化执行。异常被捕获以返回结果字典。

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
            scenario_handlers[step]()
            duration = time.time() - start_time
            result["steps"].append({
                "step": step,
                "status": "passed",
                "duration": duration
            })
        except Exception as e:
            duration = time.time() - start_time
            result["status"] = "failed"
            result["error"] = str(e)
            result["steps"].append({
                "step": step,
                "status": "failed",
                "error": str(e),
                "duration": duration
            })
            break

    return result


def run_functional_test_suite(client: Client) -> List[Dict[str, Any]]:
    """
    Run complete functional test suite / 运行完整功能测试套件

    Note: This is used for programmatic execution, not by pytest directly.
    注意: 这用于程序化执行，而不是被 pytest 直接使用。

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
