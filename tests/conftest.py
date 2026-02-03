"""
Pytest Configuration File / Pytest 配置文件
全局测试配置和fixture定义
"""
import pytest
from typing import Dict, Any
import os
import sys
import json
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# 全局测试状态存储
class TestState:
    """Test state manager / 测试状态管理器"""
    def __init__(self):
        self.flash_test_passed = False
        self.interface_test_passed = False
        self.function_test_passed = False
        self.results: Dict[str, Any] = {}

    def mark_flash_passed(self):
        self.flash_test_passed = True

    def mark_interface_passed(self):
        self.interface_test_passed = True

    def mark_function_passed(self):
        self.function_test_passed = True


@pytest.fixture(scope="session")
def test_state():
    """Test state fixture for managing test dependencies / 测试状态fixture，用于管理测试依赖"""
    return TestState()


@pytest.fixture(scope="session")
def test_config():
    """Load test configuration / 加载测试配置"""
    config_path = project_root / "configs" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope="session")
def test_artifacts_dir():
    """Create and return test artifacts directory / 创建并返回测试产物目录"""
    artifacts_dir = project_root / "test_artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    return artifacts_dir


@pytest.fixture
def temp_file(test_artifacts_dir):
    """Create a temporary file for testing / 创建临时测试文件"""
    def _create_temp_file(name: str, content: str = ""):
        temp_path = test_artifacts_dir / name
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return temp_path

    return _create_temp_file


# 依赖标记装饰器
def require_flash_test(test_func):
    """Decorator to require flash test to pass / 要求刷写测试通过的装饰器"""
    @pytest.mark.dependency(name=f"flash_required_for_{test_func.__name__}")
    def wrapper(*args, **kwargs):
        test_state = kwargs.get('test_state')
        if test_state and not test_state.flash_test_passed:
            pytest.skip("Flash test not passed yet. Skipping dependent tests.")
        return test_func(*args, **kwargs)
    return wrapper


def require_interface_test(test_func):
    """Decorator to require interface test to pass / 要求接口测试通过的装饰器"""
    @pytest.mark.dependency(name=f"interface_required_for_{test_func.__name__}")
    def wrapper(*args, **kwargs):
        test_state = kwargs.get('test_state')
        if test_state and not test_state.interface_test_passed:
            pytest.skip("Interface test not passed yet. Skipping dependent tests.")
        return test_func(*args, **kwargs)
    return wrapper


def require_function_test(test_func):
    """Decorator to require function test to pass / 要求功能测试通过的装饰器"""
    @pytest.mark.dependency(name=f"function_required_for_{test_func.__name__}")
    def wrapper(*args, **kwargs):
        test_state = kwargs.get('test_state')
        if test_state and not test_state.function_test_passed:
            pytest.skip("Function test not passed yet. Skipping dependent tests.")
        return test_func(*args, **kwargs)
    return wrapper


# 测试类别标记
pytest_marks = {
    'flash': pytest.mark.flash,           # 刷写测试
    'interface': pytest.mark.interface,   # 接口测试
    'function': pytest.mark.function,     # 功能测试
    'performance': pytest.mark.performance, # 性能测试
}


def pytest_configure(config):
    """Pytest configuration hook / Pytest配置钩子"""
    config.addinivalue_line("markers", "flash: Flash/Flash memory tests / 刷写测试")
    config.addinivalue_line("markers", "interface: Interface tests / 接口测试")
    config.addinivalue_line("markers", "function: Function tests / 功能测试")
    config.addinivalue_line("markers", "performance: Performance tests / 性能测试")
    config.addinivalue_line("markers", "dependency: Mark test dependencies / 测试依赖标记")


@pytest.fixture(autouse=True)
def log_test_start(request):
    """Auto-logging fixture for test start / 测试开始自动记录日志"""
    if request.node.get_closest_marker('flash'):
        print(f"\n{'='*60}")
        print(f"Starting FLASH test: {request.node.name}")
        print(f"{'='*60}")
    elif request.node.get_closest_marker('interface'):
        print(f"\n{'='*60}")
        print(f"Starting INTERFACE test: {request.node.name}")
        print(f"{'='*60}")
    elif request.node.get_closest_marker('function'):
        print(f"\n{'='*60}")
        print(f"Starting FUNCTION test: {request.node.name}")
        print(f"{'='*60}")
    elif request.node.get_closest_marker('performance'):
        print(f"\n{'='*60}")
        print(f"Starting PERFORMANCE test: {request.node.name}")
        print(f"{'='*60}")
