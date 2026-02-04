"""
Interface Test Configuration / 接口测试配置
接口测试的fixture和hook定义
"""
import pytest


@pytest.fixture(scope="session")
def interface_test_passed(test_state):
    """
    Interface test status fixture / 接口测试状态fixture

    Returns True if interface test has passed, otherwise False
    如果接口测试通过返回True，否则返回False
    """
    return test_state.interface_test_passed


@pytest.fixture(scope="session")
def interface_test_result(test_artifacts_dir):
    """
    Load interface test result from file / 从文件加载接口测试结果

    Args:
        test_artifacts_dir: Test artifacts directory / 测试产物目录

    Returns:
        dict: Interface test result or None / 接口测试结果或None
    """
    import json
    from pathlib import Path

    result_file = test_artifacts_dir / "interface_test_result.json"
    if result_file.exists():
        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None
