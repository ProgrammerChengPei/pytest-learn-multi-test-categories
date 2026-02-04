"""
Performance Test Cases / 性能测试用例
使用全名 nodeid 进行依赖声明，验证跨文件依赖
"""
import pytest


class TestPerformance:
    """Performance test class / 性能测试类"""

    @pytest.mark.performance
    @pytest.mark.dependency(
        name="tests2.performance_tests.test_performance.TestPerformance#test_performance_latency",
        depends=["tests2.function_tests.test_function.TestFunction#test_function_complete"]
    )
    def test_performance_latency(self):
        """
        Test performance latency / 测试性能延迟

        依赖完整的 nodeid: tests2.function_tests.test_function.TestFunction#test_function_complete
        """
        print("✓ test_performance_latency 执行")
        assert True

    @pytest.mark.performance
    @pytest.mark.dependency(
        name="tests2.performance_tests.test_performance.TestPerformance#test_performance_throughput",
        depends=["tests2.performance_tests.test_performance.TestPerformance#test_performance_latency"]
    )
    def test_performance_throughput(self):
        """
        Test performance throughput / 测试性能吞吐量

        依赖同文件的完整 nodeid
        """
        print("✓ test_performance_throughput 执行")
        assert True

    @pytest.mark.performance
    @pytest.mark.dependency(
        name="tests2.performance_tests.test_performance.TestPerformance#test_performance_complete",
        depends=["tests2.performance_tests.test_performance.TestPerformance#test_performance_throughput"]
    )
    def test_performance_complete(self):
        """
        Test performance completion / 测试性能完成

        使用完整的 nodeid 作为依赖名称
        """
        print("✓ test_performance_complete 执行（标记为依赖目标）")
        assert True
