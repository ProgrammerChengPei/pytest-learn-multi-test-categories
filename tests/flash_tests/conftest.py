"""
Flash Test Configuration / 刷写测试配置
Flash测试的fixture和hook定义
"""
import pytest


@pytest.fixture(scope="session")
def flash_test_passed(test_state):
    """
    Flash test status fixture / 刷写测试状态fixture

    Returns True if flash test has passed, otherwise False
    如果刷写测试通过返回True，否则返回False
    """
    return test_state.flash_test_passed


@pytest.fixture(scope="session")
def flash_test_result(test_artifacts_dir):
    """
    Load flash test result from file / 从文件加载刷写测试结果

    Args:
        test_artifacts_dir: Test artifacts directory / 测试产物目录

    Returns:
        dict: Flash test result or None / 刷写测试结果或None
    """
    import json
    from pathlib import Path

    result_file = test_artifacts_dir / "flash_test_result.json"
    if result_file.exists():
        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None
