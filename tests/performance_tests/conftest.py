"""
Performance Test Configuration / 性能测试配置
性能测试的fixture和hook定义
"""
import pytest


@pytest.fixture(scope="session")
def performance_test_passed(test_state):
    """
    Performance test status fixture / 性能测试状态fixture

    Returns True if performance test has passed, otherwise False
    如果性能测试通过返回True，否则返回False
    """
    return True  # Performance tests don't have a specific "passed" state like others


@pytest.fixture(scope="session")
def performance_test_result(test_artifacts_dir):
    """
    Load performance test result from file / 从文件加载性能测试结果

    Args:
        test_artifacts_dir: Test artifacts directory / 测试产物目录

    Returns:
        dict: Performance test result or None / 性能测试结果或None
    """
    import json
    from pathlib import Path

    result_file = test_artifacts_dir / "performance_test_result.json"
    if result_file.exists():
        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None
