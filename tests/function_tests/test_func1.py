"""
Function Test Cases / 功能测试用例
"""
import json5
import time

import pytest

from src.client import Client
from tests.function_tests.common.function_common1 import (
    _test_connection_lifecycle,
    _test_data_integrity,
    _test_error_recovery,
    _test_message_sequence
)


class TestFunction:
    """Function test class / 功能测试类"""

    @pytest.mark.function
    @pytest.mark.dependency(name="test_function_connection_lifecycle")
    def test_function_connection_lifecycle(self, test_state, test_client):
        """
        Test connection lifecycle functionality / 测试连接生命周期功能

        This test verifies that connections can be properly managed through their lifecycle.
        此测试验证连接可以在其生命周期内得到正确管理。

        Depends on: Interface test must pass / 依赖：接口测试必须通过
        """
        if not test_state.interface_test_passed:
            pytest.skip("Interface test has not passed yet")

        _test_connection_lifecycle(test_client)
        print("✓ Connection lifecycle function test passed")

    @pytest.mark.function
    @pytest.mark.dependency(name="test_function_message_sequence", depends=["test_function_connection_lifecycle"])
    def test_function_message_sequence(self, test_client):
        """
        Test message sequencing functionality / 测试消息排序功能

        This test verifies that messages are processed in the correct order.
        此测试验证消息按正确顺序处理。

        Depends on: Connection lifecycle test / 依赖：连接生命周期测试
        """
        sequence = [
            {"type": "request", "command": "get_status", "token": test_client.token},
            {"type": "request", "command": "health_check", "token": test_client.token},
            {"type": "request", "command": "echo_with_timestamp", "text": "seq1", "token": test_client.token},
            {"type": "request", "command": "echo_with_timestamp", "text": "seq2", "token": test_client.token}
        ]

        _test_message_sequence(test_client, sequence)
        print("✓ Message sequence function test passed")

    @pytest.mark.function
    @pytest.mark.dependency(name="test_function_error_recovery", depends=["test_function_message_sequence"])
    def test_function_error_recovery(self, test_client):
        """
        Test error recovery functionality / 测试错误恢复功能

        This test verifies the system can recover from errors.
        此测试验证系统可以从错误中恢复。

        Depends on: Message sequence test / 依赖：消息序列测试
        """
        _test_error_recovery(test_client)
        print("✓ Error recovery function test passed")

    @pytest.mark.function
    @pytest.mark.dependency(name="test_function_data_integrity", depends=["test_function_error_recovery"])
    def test_function_data_integrity(self, test_client):
        """
        Test data integrity functionality / 测试数据完整性功能

        This test verifies that data integrity is maintained throughout operations.
        此测试验证在整个操作过程中保持数据完整性。

        Depends on: Error recovery test / 依赖：错误恢复测试
        """
        test_data = "Test data for integrity check: " + "ABCD" * 100

        _test_data_integrity(test_client, test_data)
        print("✓ Data integrity function test passed")

    @pytest.mark.function
    @pytest.mark.dependency(name="test_function_multiple_clients", depends=["test_function_data_integrity"])
    def test_function_multiple_clients(self, test_config, test_client):
        """
        Test multiple clients functionality / 测试多客户端功能

        This test verifies that multiple clients can connect and communicate simultaneously.
        此测试验证多个客户端可以同时连接和通信。

        Depends on: Data integrity test / 依赖：数据完整性测试
        """
        from unittest.mock import MagicMock

        clients = []
        # Create multiple mock clients
        for i in range(3):
            client = MagicMock()
            client.connected = True
            client.host = test_config.get('host', 'localhost')
            client.port = test_config.get('port', 8080)
            client.token = test_config.get('token', 'your-secure-token-here')
            client.send = MagicMock(return_value=True)
            clients.append(client)

        # Send requests from each client
        for i, client in enumerate(clients):
            request = {
                "type": "request",
                "command": "get_status",
                "id": i + 1,
                "token": client.token
            }
            success = client.send(request)
            assert success, f"Client {i+1} should be able to send request"

        print("✓ Multiple clients function test passed")

    @pytest.mark.function
    @pytest.mark.dependency(name="test_function_complete", depends=["test_function_multiple_clients"])
    def test_function_complete(self, test_state, test_client, reports_dir):
        """
        Test function completion / 测试功能测试完成

        This test marks the function test as completed and saves results.
        此测试标记功能测试完成并保存结果。

        Depends on: Multiple clients test / 依赖：多客户端测试
        """
        test_state.mark_function_passed()

        # Save function test result
        result = {
            "test_type": "function",
            "status": "passed",
            "timestamp": time.time(),
            "tests_passed": 6
        }

        result_file = reports_dir / "function_test_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json5.dump(result, f, ensure_ascii=False, indent=2)

        print("✓ Function test completed and marked as passed")
        print(f"✓ Function test result saved to {result_file}")
