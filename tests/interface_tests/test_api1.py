"""
Interface Test Cases / 接口测试用例
"""
import json
import time

import pytest

from tests.interface_tests.common.interface_common1 import (
    batch_send_requests,
    calculate_success_rate,
    compare_timestamps,
    measure_request_latency,
    send_and_receive,
    validate_response_status,
    validate_response_structure
)


class TestInterface:
    """Interface test class / 接口测试类"""

    @pytest.mark.interface
    def test_interface_get_status(self, test_state, test_client, test_config):
        """
        Test get_status interface / 测试get_status接口

        This test verifies get_status command returns correct structure and data.
        此测试验证get_status命令返回正确的结构和数据。

        Depends on: Flash test must pass / 依赖：刷写测试必须通过
        """
        if not test_state.flash_test_passed:
            pytest.skip("Flash test has not passed yet")

        request = {
            "type": "request",
            "command": "get_status",
            "id": 1,
            "token": test_client.token
        }

        server_timeout = test_config.get('server_timeout', 5.0)
        response = send_and_receive(test_client, request, timeout=server_timeout)

        # Validate structure
        expected_fields = ["type", "id", "status", "server_time", "connections"]
        assert validate_response_structure(response, expected_fields), \
            f"Response missing expected fields. Got: {response}"

        # Validate status
        assert validate_response_status(response, "ok"), \
            f"Status should be 'ok', got: {response.get('status')}"

        # Validate connections count
        assert isinstance(response.get('connections'), int), \
            "Connections should be an integer"

        print("✓ get_status interface test passed")

    @pytest.mark.interface
    def test_interface_health_check(self, test_state, test_client, test_config):
        """
        Test health_check interface / 测试health_check接口

        This test verifies health_check command returns healthy status.
        此测试验证health_check命令返回健康状态。

        Depends on: get_status test / 依赖：get_status测试
        """
        request = {
            "type": "request",
            "command": "health_check",
            "id": 2,
            "token": test_client.token
        }

        server_timeout = test_config.get('server_timeout', 5.0)
        response = send_and_receive(test_client, request, timeout=server_timeout)

        # Validate structure
        expected_fields = ["type", "id", "status"]
        assert validate_response_structure(response, expected_fields), \
            f"Response missing expected fields. Got: {response}"

        # Validate status
        assert validate_response_status(response, "healthy"), \
            f"Status should be 'healthy', got: {response.get('status')}"

        print("✓ health_check interface test passed")

    @pytest.mark.interface
    def test_interface_echo(self, test_state, test_client, test_config):
        """
        Test echo_with_timestamp interface / 测试echo_with_timestamp接口

        This test verifies echo command returns original text with server timestamp.
        此测试验证echo命令返回原始文本和服务器时间戳。

        Depends on: health_check test / 依赖：health_check测试
        """
        test_text = "Hello, Server!"
        request = {
            "type": "request",
            "command": "echo_with_timestamp",
            "id": 3,
            "text": test_text,
            "token": test_client.token
        }

        server_timeout = test_config.get('server_timeout', 5.0)
        response = send_and_receive(test_client, request, timeout=server_timeout)

        # Validate structure
        expected_fields = ["type", "id", "status", "original_text", "server_response", "server_timestamp"]
        assert validate_response_structure(response, expected_fields), \
            f"Response missing expected fields. Got: {response}"

        # Validate status
        assert validate_response_status(response, "ok"), \
            f"Status should be 'ok', got: {response.get('status')}"

        # Validate original text is preserved
        assert response.get('original_text') == test_text, \
            f"Original text not preserved. Expected: {test_text}, Got: {response.get('original_text')}"

        # Validate timestamp format
        server_timestamp = response.get('server_timestamp')
        assert server_timestamp and isinstance(server_timestamp, str), \
            f"Server timestamp should be a string. Got: {server_timestamp}"

        # Validate timestamp is recent
        assert compare_timestamps(server_timestamp, time.time(), tolerance=60.0), \
            f"Server timestamp is not recent: {server_timestamp}"

        print("✓ echo_with_timestamp interface test passed")

    @pytest.mark.interface
    def test_interface_batch_requests(self, test_state, test_client, test_config):
        """
        Test batch interface requests / 测试批量接口请求

        This test verifies that multiple requests can be sent and processed correctly.
        此测试验证可以正确发送和处理多个请求。

        Depends on: echo test / 依赖：echo测试
        """
        requests = [
            {"type": "request", "command": "get_status", "id": 10, "token": test_client.token},
            {"type": "request", "command": "health_check", "id": 11, "token": test_client.token},
            {"type": "request", "command": "health_check", "id": 12, "token": test_client.token}
        ]

        responses = batch_send_requests(test_client, requests, delay=0.2, test_config=test_config)

        # Validate all responses received
        assert len(responses) == len(requests), \
            f"Expected {len(requests)} responses, got {len(responses)}"

        # Validate success rate
        success_rate = calculate_success_rate(responses)
        assert success_rate >= 90.0, \
            f"Success rate should be >= 90%, got: {success_rate}%"

        print(f"✓ Batch requests test passed (success rate: {success_rate}%)")

    @pytest.mark.interface
    def test_interface_latency(self, test_state, test_client, test_config):
        """
        Test interface request latency / 测试接口请求延迟

        This test measures and validates request latency.
        此测试测量并验证请求延迟。

        Depends on: batch requests test / 依赖：批量请求测试
        """
        request = {
            "type": "request",
            "command": "health_check",
            "id": 20,
            "token": test_client.token
        }

        latencies = []
        for _ in range(10):
            latency = measure_request_latency(test_client, request, test_config=test_config)
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)

        assert avg_latency < 1.0, \
            f"Average latency should be < 1.0s, got: {avg_latency:.3f}s"

        assert max_latency < 2.0, \
            f"Max latency should be < 2.0s, got: {max_latency:.3f}s"

        print(f"✓ Interface latency test passed (avg: {avg_latency:.3f}s, max: {max_latency:.3f}s)")

    @pytest.mark.interface
    def test_interface_complete(self, test_state, test_client, reports_dir):
        """
        Test interface completion / 测试接口测试完成

        This test marks interface test as completed and saves results.
        此测试标记接口测试完成并保存结果。

        Depends on: latency test / 依赖：延迟测试
        """
        test_state.mark_interface_passed()

        # Save interface test result
        result = {
            "test_type": "interface",
            "status": "passed",
            "timestamp": time.time(),
            "tests_passed": 5
        }

        result_file = reports_dir / "interface_test_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print("✓ Interface test completed and marked as passed")
        print(f"✓ Interface test result saved to {result_file}")
