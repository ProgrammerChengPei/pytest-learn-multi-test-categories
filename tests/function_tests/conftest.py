"""
Function Test Configuration / 功能测试配置
功能测试的fixture和hook定义
"""
import pytest


@pytest.fixture(scope="session")
def function_test_passed(test_state):
    """
    Function test status fixture / 功能测试状态fixture

    Returns True if function test has passed, otherwise False
    如果功能测试通过返回True，否则返回False
    """
    return test_state.function_test_passed


@pytest.fixture(scope="session")
def function_test_result(reports_dir):
    """
    Load function test result from file / 从文件加载功能测试结果

    Args:
        reports_dir: reports directory / 测试报告目录

    Returns:
        dict: Function test result or None / 功能测试结果或None
    """
    import json5
    from pathlib import Path

    result_file = reports_dir / "function_test_result.json"
    if result_file.exists():
        with open(result_file, 'r', encoding='utf-8') as f:
            return json5.load(f)
    return None
