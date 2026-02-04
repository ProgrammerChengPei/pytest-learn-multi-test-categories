"""
Performance Test Cases / 性能测试用例
"""
import json
import time

import pytest

from src.client import Client
from tests.performance_tests.common.common import (concurrent_test,
                                                   measure_latency,
                                                   measure_throughput,
                                                   run_performance_suite,
                                                   stress_test)


class TestPerformance:
    """Performance test class / 性能测试类"""

    @pytest.mark.performance
    @pytest.mark.dependency(name="test_performance_latency", depends=["test_function_complete"])
    def test_performance_latency(self, test_state, test_client, function_test_passed):
        """
        Test request latency performance / 测试请求延迟性能

        This test measures the latency of various requests and ensures they meet performance targets.
        此测试测量各种请求的延迟并确保它们满足性能目标。

        Depends on: Function test must pass / 依赖：功能测试必须通过
        """
        if not function_test_passed:
            pytest.skip("Function test has not passed yet")

        commands = [
            {"type": "request", "command": "get_status", "token": Client.token},
            {"type": "request", "command": "health_check", "token": Client.token},
            {"type": "request", "command": "echo_with_timestamp", "text": "test", "token": Client.token}
        ]

        latencies = {}

        try:
            for request in commands:
                command = request.get('command')
                result = measure_latency(test_client, request, iterations=30)
                result.calculate_metrics()

                latencies[command] = {
                    "avg": result.percentiles.get('avg', 0),
                    "p50": result.percentiles.get('p50', 0),
                    "p95": result.percentiles.get('p95', 0),
                    "p99": result.percentiles.get('p99', 0)
                }

                # Validate performance targets
                assert result.percentiles.get('p95', 0) < 1.0, \
                    f"{command} P95 latency should be < 1.0s, got: {result.percentiles.get('p95', 0):.3f}s"

                print(f"✓ {command} latency test passed (avg: {result.percentiles.get('avg', 0):.3f}s, "
                      f"p95: {result.percentiles.get('p95', 0):.3f}s)")

        except Exception as e:
            print(f"✗ Latency performance test failed: {e}")
            raise

    @pytest.mark.performance
    @pytest.mark.dependency(name="test_performance_throughput", depends=["test_performance_latency"])
    def test_performance_throughput(self, test_state, test_client):
        """
        Test throughput performance / 测试吞吐量性能

        This test measures the system's throughput under various load conditions.
        此测试测量系统在各种负载条件下的吞吐量。

        Depends on: Latency test / 依赖：延迟测试
        """
        request = {
            "type": "request",
            "command": "health_check",
            "token": Client.token
        }

        try:
            # Test with different target throughput levels
            target_rps_values = [10, 20, 30]
            throughput_results = []

            for target_rps in target_rps_values:
                result = measure_throughput(test_client, request, duration=5, target_rps=target_rps)
                result.calculate_metrics()

                actual_throughput = result.throughput
                throughput_results.append({
                    "target_rps": target_rps,
                    "actual_rps": actual_throughput,
                    "success_rate": result.successful_requests / result.total_requests * 100 if result.total_requests > 0 else 0
                })

                # Validate throughput (should achieve at least 80% of target)
                assert actual_throughput >= target_rps * 0.8, \
                    f"Throughput should be >= {target_rps * 0.8} RPS, got: {actual_throughput:.2f} RPS"

                print(f"✓ Throughput test passed (target: {target_rps} RPS, "
                      f"actual: {actual_throughput:.2f} RPS)")

        except Exception as e:
            print(f"✗ Throughput performance test failed: {e}")
            raise

    @pytest.mark.performance
    @pytest.mark.dependency(name="test_performance_concurrent", depends=["test_performance_throughput"])
    def test_performance_concurrent(self, test_state, test_config, function_test_passed):
        """
        Test concurrent performance / 测试并发性能

        This test measures performance under concurrent load.
        此测试测量并发负载下的性能。

        Depends on: Throughput test / 依赖：吞吐量测试
        """
        

        try:
            result = concurrent_test(
                lambda: Client(
                    test_config.get('host', 'localhost'),
                    test_config.get('port', 8080),
                    test_config.get('token', 'your-secure-token-here')
                ),
                num_clients=3,
                requests_per_client=15
            )
            result.calculate_metrics()

            # Validate concurrent performance
            assert result.successful_requests > 0, "Should have successful requests"
            assert result.throughput > 0, "Should have positive throughput"

            success_rate = result.successful_requests / result.total_requests * 100 if result.total_requests > 0 else 0
            assert success_rate >= 90, f"Success rate should be >= 90%, got: {success_rate:.2f}%"

            print(f"✓ Concurrent performance test passed (throughput: {result.throughput:.2f} RPS, "
                  f"success rate: {success_rate:.2f}%)")

        except Exception as e:
            print(f"✗ Concurrent performance test failed: {e}")
            raise

    @pytest.mark.performance
    @pytest.mark.dependency(name="test_performance_stress", depends=["test_performance_concurrent"])
    def test_performance_stress(self, test_state, test_client):
        """
        Test stress performance / 测试压力性能

        This test measures system performance under sustained high load.
        此测试测量持续高负载下的系统性能。

        Depends on: Concurrent test / 依赖：并发测试
        """
        try:
            result = stress_test(test_client, max_requests=200, max_duration=60)
            result.calculate_metrics()

            # Validate stress test results
            assert result.total_requests > 0, "Should have processed requests"
            assert result.successful_requests > 0, "Should have successful requests"

            success_rate = result.successful_requests / result.total_requests * 100 if result.total_requests > 0 else 0
            assert success_rate >= 95, f"Success rate should be >= 95%, got: {success_rate:.2f}%"

            print(f"✓ Stress performance test passed (total: {result.total_requests}, "
                  f"successful: {result.successful_requests}, success rate: {success_rate:.2f}%)")

        except Exception as e:
            print(f"✗ Stress performance test failed: {e}")
            raise

    @pytest.mark.performance
    @pytest.mark.dependency(name="test_performance_complete", depends=["test_performance_stress"])
    def test_performance_complete(self, test_state, test_client, test_artifacts_dir):
        """
        Test performance completion / 测试性能测试完成

        This test runs the complete performance suite and saves results.
        此测试运行完整性能套件并保存结果。

        Depends on: Stress test / 依赖：压力测试
        """
        try:
            # Run complete performance suite
            results = run_performance_suite(test_client)

            # Aggregate results
            summary = {
                "test_type": "performance",
                "status": "passed",
                "timestamp": time.time(),
                "total_tests": len(results),
                "tests_passed": len([r for r in results if r.failed_requests == 0]),
                "results": [r.to_dict() for r in results]
            }

            # Save performance test result
            result_file = test_artifacts_dir / "performance_test_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            print(f"✓ Performance test suite completed ({summary['tests_passed']}/{summary['total_tests']} tests passed)")
            print(f"✓ Performance test result saved to {result_file}")

        except Exception as e:
            print(f"✗ Performance test suite failed: {e}")
            raise
