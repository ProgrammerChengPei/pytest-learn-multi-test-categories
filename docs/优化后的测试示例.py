"""
优化后的接口测试示例 / Optimized Interface Test Example
展示如何使用公共辅助函数和简化装饰器 / Demonstrates usage of common helpers and simplified decorators
"""
import pytest
import time
from tests.common.common import (
    interface_test_marker,      # 接口测试标记
    require_flash_test,         # 依赖刷写测试
    send_and_receive,           # 发送并接收
    validate_response_structure, # 验证响应结构
    validate_response_status,    # 验证响应状态
    compare_timestamps,         # 比较时间戳
    batch_send_requests,        # 批量发送请求
    calculate_success_rate,      # 计算成功率
    assert_response_success,     # 断言响应成功
    assert_in_range,            # 断言值在范围内
)


class TestInterface:
    """接口测试类 / Interface test class"""

    @interface_test_marker
    @require_flash_test
    def test_interface_get_status(self, test_state, test_client):
        """
        Test get_status interface / 测试get_status接口

        注意：此测试自动要求刷写测试通过，无需手动检查
        Note: This test automatically requires flash test to pass, no manual check needed
        """
        request = {
            "type": "request",
            "command": "get_status",
            "id": 1,
            "token": test_client.token
        }

        response = send_and_receive(test_client, request, timeout=10.0)

        # 验证结构 / Validate structure
        expected_fields = ["type", "id", "status", "server_time", "connections"]
        assert validate_response_structure(response, expected_fields), \
            f"Response missing expected fields. Got: {response}"

        # 验证状态 / Validate status
        assert validate_response_status(response, "ok"), \
            f"Status should be 'ok', got: {response.get('status')}"

        # 验证连接数 / Validate connections count
        assert isinstance(response.get('connections'), int), \
            "Connections should be an integer"

        print("✓ get_status interface test passed")

    @interface_test_marker
    @require_flash_test
    def test_interface_health_check(self, test_state, test_client):
        """Test health_check interface / 测试health_check接口"""
        request = {
            "type": "request",
            "command": "health_check",
            "id": 2,
            "token": test_client.token
        }

        response = send_and_receive(test_client, request, timeout=10.0)

        expected_fields = ["type", "id", "status"]
        assert validate_response_structure(response, expected_fields)
        assert validate_response_status(response, "healthy")

        print("✓ health_check interface test passed")

    @interface_test_marker
    @require_flash_test
    def test_interface_echo(self, test_state, test_client):
        """Test echo_with_timestamp interface / 测试echo_with_timestamp接口"""
        test_text = "Hello, Server!"
        request = {
            "type": "request",
            "command": "echo_with_timestamp",
            "id": 3,
            "text": test_text,
            "token": test_client.token
        }

        response = send_and_receive(test_client, request, timeout=10.0)

        expected_fields = ["type", "id", "status", "original_text", "server_response", "server_timestamp"]
        assert validate_response_structure(response, expected_fields)
        assert validate_response_status(response, "ok")
        assert response.get('original_text') == test_text, \
            f"Original text not preserved. Expected: {test_text}, Got: {response.get('original_text')}"

        # 使用公共函数比较时间戳 / Use common function to compare timestamps
        assert compare_timestamps(response.get('server_timestamp'), time.time(), tolerance=60.0), \
            f"Server timestamp is not recent: {response.get('server_timestamp')}"

        print("✓ echo_with_timestamp interface test passed")

    @interface_test_marker
    @require_flash_test
    def test_interface_batch_requests(self, test_state, test_client):
        """Test batch interface requests / 测试批量接口请求"""
        requests = [
            {"type": "request", "command": "get_status", "id": 10, "token": test_client.token},
            {"type": "request", "command": "health_check", "id": 11, "token": test_client.token},
            {"type": "request", "command": "health_check", "id": 12, "token": test_client.token}
        ]

        responses = batch_send_requests(test_client, requests, delay=0.2)

        assert len(responses) == len(requests), \
            f"Expected {len(requests)} responses, got {len(responses)}"

        success_rate = calculate_success_rate(responses)
        assert success_rate >= 90.0, \
            f"Success rate should be >= 90%, got: {success_rate}%"

        print(f"✓ Batch requests test passed (success rate: {success_rate}%)")

    @interface_test_marker
    @require_flash_test
    def test_interface_latency(self, test_state, test_client):
        """Test interface request latency / 测试接口请求延迟"""
        request = {
            "type": "request",
            "command": "health_check",
            "id": 20,
            "token": test_client.token
        }

        # 使用公共辅助函数测量延迟 / Use common helper to measure latency
        latencies = []
        for _ in range(10):
            latency = send_and_receive.__wrapped__(test_client, request)
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)

        # 使用公共断言助手 / Use common assertion helper
        assert_in_range(avg_latency, 0, 1.0, "Average latency")
        assert_in_range(max_latency, 0, 2.0, "Maximum latency")

        print(f"✓ Interface latency test passed (avg: {avg_latency:.3f}s, max: {max_latency:.3f}s)")


# ============================================================================
# 优化对比 / Optimization Comparison
# ============================================================================

"""
原始写法 (冗长) / Original Approach (Verbose):
-----------------------------------------------
@pytest.mark.interface
@pytest.mark.dependency(name="test_xxx", depends=["test_flash_complete"])
def test_xxx(self, test_state, test_client, flash_test_passed):
    if not flash_test_passed:
        pytest.skip("Flash test has not passed yet")
    # 测试代码...
    pass

优化写法 (简洁) / Optimized Approach (Concise):
-----------------------------------------------
@interface_test_marker
@require_flash_test
def test_xxx(self, test_state, test_client):
    # 测试代码...
    pass

优势 / Advantages:
1. 代码行数减少约 35-40% / Code reduced by 35-40%
2. 依赖检查自动处理 / Dependency check automatically handled
3. 更清晰的意图表达 / Clearer intent expression
4. 更容易维护 / Easier to maintain
"""


# ============================================================================
# 公共辅助函数使用示例 / Common Helper Functions Usage Examples
# ============================================================================

class TestInterfaceAdvanced:
    """高级接口测试示例 / Advanced interface test examples"""

    @interface_test_marker
    @require_flash_test
    def test_with_response_success_assertion(self, test_state, test_client):
        """使用响应成功断言助手 / Using response success assertion helper"""
        request = {
            "type": "request",
            "command": "health_check",
            "id": 1,
            "token": test_client.token
        }

        response = send_and_receive(test_client, request, timeout=10.0)

        # 使用公共断言函数 / Use common assertion function
        assert_response_success(response, "health_check")

    @interface_test_marker
    @require_flash_test
    def test_with_range_assertion(self, test_state, test_client):
        """使用范围断言助手 / Using range assertion helper"""
        from tests.common.common import measure_request_latency

        request = {
            "type": "request",
            "command": "health_check",
            "id": 1,
            "token": test_client.token
        }

        latency = measure_request_latency(test_client, request)

        # 使用公共断言函数 / Use common assertion function
        assert_in_range(latency, 0, 1.0, "Request latency")

    @interface_test_marker
    @require_flash_test
    def test_data_integrity(self, test_state, test_client):
        """使用数据完整性测试 / Using data integrity test"""
        from tests.common.common import test_data_integrity

        test_data = "Test data for integrity: " + "ABCD" * 100

        # 使用公共函数 / Use common function
        result = test_data_integrity(test_client, test_data)
        assert result, "Data integrity test should pass"

    @interface_test_marker
    @require_flash_test
    def test_batch_with_high_success_rate(self, test_state, test_client):
        """批量请求高成功率测试 / Batch request high success rate test"""
        # 生成更多请求 / Generate more requests
        requests = [
            {"type": "request", "command": "health_check", "id": i, "token": test_client.token}
            for i in range(20, 40)
        ]

        responses = batch_send_requests(test_client, requests, delay=0.1)

        success_rate = calculate_success_rate(responses)

        # 使用公共断言函数 / Use common assertion function
        assert_in_range(success_rate, 95.0, 100.0, "Success rate")

        print(f"✓ High success rate test passed: {success_rate:.2f}%")


# ============================================================================
# 完整测试套件示例 / Complete Test Suite Example
# ============================================================================

"""
# 可以这样组织完整的测试类 / Organize complete test class like this:

class TestInterfaceComplete:
    '''完整的接口测试套件 / Complete interface test suite'''

    # 所有测试自动依赖刷写测试
    # All tests automatically depend on flash test
    @pytest.fixture(autouse=True)
    def setup(self, test_state):
        '''可选：测试前置设置 / Optional: Test setup'''
        pass

    # 测试1: get_status
    @interface_test_marker
    @require_flash_test
    def test_01_get_status(self, test_state, test_client):
        pass

    # 测试2: health_check
    @interface_test_marker
    @require_flash_test
    def test_02_health_check(self, test_state, test_client):
        pass

    # 测试3-10: 其他测试...
    # Tests 3-10: Other tests...
"""
