"""
Function Test Cases / 功能测试用例
"""
import json
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
    def test_function_connection_lifecycle(self, test_client, test_state, interface_test_passed):
        """
        Test connection lifecycle functionality / 测试连接生命周期功能

        This test verifies that connections can be properly managed through their lifecycle.
        此测试验证连接可以在其生命周期内得到正确管理。

        Depends on: Interface test must pass / 依赖：接口测试必须通过
        """
        if not interface_test_passed:
            pytest.skip("Interface test has not passed yet")

        try:
            result = _test_connection_lifecycle(test_client)
            assert result, "Connection lifecycle test should pass"
            print("✓ Connection lifecycle function test passed")

        except Exception as e:
            print(f"✗ Connection lifecycle function test failed: {e}")
            raise

    @pytest.mark.function
    @pytest.mark.dependency(name="test_function_message_sequence", depends=["test_function_connection_lifecycle"])
    def test_function_message_sequence(self, test_state, test_client):
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

        try:
            result = _test_message_sequence(test_client, sequence)
            assert result, "Message sequence test should pass"
            print("✓ Message sequence function test passed")

        except Exception as e:
            print(f"✗ Message sequence function test failed: {e}")
            raise

    @pytest.mark.function
    @pytest.mark.dependency(name="test_function_error_recovery", depends=["test_function_message_sequence"])
    def test_function_error_recovery(self, test_state, test_client):
        """
        Test error recovery functionality / 测试错误恢复功能

        This test verifies the system can recover from errors.
        此测试验证系统可以从错误中恢复。

        Depends on: Message sequence test / 依赖：消息序列测试
        """
        try:
            result = _test_error_recovery(test_client)
            assert result, "Error recovery test should pass"
            print("✓ Error recovery function test passed")

        except Exception as e:
            print(f"✗ Error recovery function test failed: {e}")
            raise

    @pytest.mark.function
    @pytest.mark.dependency(name="test_function_data_integrity", depends=["test_function_error_recovery"])
    def test_function_data_integrity(self, test_state, test_client):
        """
        Test data integrity functionality / 测试数据完整性功能

        This test verifies that data integrity is maintained throughout operations.
        此测试验证在整个操作过程中保持数据完整性。

        Depends on: Error recovery test / 依赖：错误恢复测试
        """
        test_data = "Test data for integrity check: " + "ABCD" * 100

        try:
            result = _test_data_integrity(test_client, test_data)
            assert result, "Data integrity test should pass"
            print("✓ Data integrity function test passed")

        except Exception as e:
            print(f"✗ Data integrity function test failed: {e}")
            raise

    @pytest.mark.function
    @pytest.mark.dependency(name="test_function_multiple_clients", depends=["test_function_data_integrity"])
    def test_function_multiple_clients(self, test_state, test_config, interface_test_passed):
        """
        Test multiple clients functionality / 测试多客户端功能

        This test verifies that multiple clients can connect and communicate simultaneously.
        此测试验证多个客户端可以同时连接和通信。

        Depends on: Data integrity test / 依赖：数据完整性测试
        """
        clients = []
        try:
            # Create multiple clients
            for i in range(3):
                client = Client(
                    test_config.get('host', 'localhost'),
                    test_config.get('port', 8080),
                    test_config.get('token', 'your-secure-token-here')
                )
                assert client.connected, f"Client {i+1} should be connected"
                clients.append(client)

            # Send requests from each client
            for i, client in enumerate(clients):
                request = {
                    "type": "request",
                    "command": "get_status",
                    "id": i + 1,
                    "token": test_config.get('token', 'your-secure-token-here')
                }
                success = client.send(request)
                assert success, f"Client {i+1} should be able to send request"

            print("✓ Multiple clients function test passed")

        finally:
            for client in clients:
                client.close()

    @pytest.mark.function
    @pytest.mark.dependency(name="test_function_complete", depends=["test_function_multiple_clients"])
    def test_function_complete(self, test_state, test_client, test_artifacts_dir):
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

        result_file = test_artifacts_dir / "function_test_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print("✓ Function test completed and marked as passed")
        print(f"✓ Function test result saved to {result_file}")
