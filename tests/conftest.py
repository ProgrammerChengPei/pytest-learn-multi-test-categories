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


# ============================================================================
# 自动依赖管理钩子 / Automatic Dependency Management Hooks
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """
    自动添加测试依赖标记 / Automatically add test dependency markers

    使用钩子自动管理测试依赖，避免在每个测试上手动添加装饰器
    Use hooks to automatically manage test dependencies, avoiding manual decorators

    依赖规则 / Dependency Rules:
    - 接口测试 (interface) → 依赖刷写测试完成 (test_flash_complete)
    - 功能测试 (function) → 依赖接口测试完成 (test_interface_complete)
    - 性能测试 (performance) → 依赖功能测试完成 (test_function_complete)

    Args:
        config: Pytest configuration / Pytest配置
        items: List of collected test items / 收集的测试项列表
    """
    # 获取test_state（如果已经创建）
    # Get test_state (if already created)
    test_state = None
    try:
        # 尝试从fixture manager获取 / Try to get from fixture manager
        if hasattr(config, '_pytest'):
            test_state = getattr(config, '_pytest', {}).get('_test_state', None)
    except Exception:
        pass

    # 定义测试阶段顺序 / Define test phase order
    phase_order = {
        'flash': 0,
        'interface': 1,
        'function': 2,
        'performance': 3
    }

    # 定义依赖映射 / Define dependency mapping
    dependency_mapping = {
        'interface': 'test_flash_complete',
        'function': 'test_interface_complete',
        'performance': 'test_function_complete'
    }

    for item in items:
        # 检查测试类型标记 / Check test type markers
        for marker_name in ['interface', 'function', 'performance']:
            if item.get_closest_marker(marker_name):
                # 添加自动依赖标记 / Add automatic dependency marker
                dependency_name = dependency_mapping.get(marker_name)
                if dependency_name:
                    # 使用pytest-dependency的内部API添加依赖
                    # Use pytest-dependency's internal API to add dependency
                    item.add_marker(
                        pytest.mark.dependency(
                            depends=[dependency_name],
                            name=f"{marker_name}_auto_dep_{item.name}"
                        )
                    )
                    # 打印调试信息 / Print debug info
                    print(f"[Auto Dependency] {item.name} → depends on {dependency_name}")
                break

    # 按测试类型排序（可选） / Sort by test type (optional)
    def get_test_order(item):
        """获取测试顺序 / Get test order"""
        for marker_name, order in phase_order.items():
            if item.get_closest_marker(marker_name):
                return order
        return 99  # 其他测试放最后 / Other tests go last

    items.sort(key=get_test_order)


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


def pytest_runtest_setup(item):
    """
    测试执行前自动检查依赖 / Automatically check dependencies before test execution

    在每个测试运行前检查前置测试是否通过，如果未通过则跳过
    Check if prerequisite tests have passed before running each test, skip if not

    Args:
        item: Test item to be executed / 要执行的测试项
    """
    # 检查测试类型 / Check test type
    test_type = None
    for marker in ['interface', 'function', 'performance']:
        if item.get_closest_marker(marker):
            test_type = marker
            break

    if not test_type:
        return  # 不是需要依赖检查的测试 / Not a test requiring dependency check

    # 获取test_state fixture / Get test_state fixture
    test_state = None
    try:
        # 使用pytest的fixture管理器 / Use pytest's fixture manager
        if hasattr(item, '_fixtureinfo'):
            fixturedef = item._fixtureinfo.name2fixturedefs.get('test_state')
            if fixturedef:
                test_state = fixturedef[0].cached_result
                if test_state:
                    test_state = test_state[0]  # 获取fixture的返回值 / Get fixture return value
    except Exception:
        pass

    # 如果无法获取test_state，跳过检查（在pytest初始化时可能会发生）
    # If test_state cannot be obtained, skip check (may happen during pytest initialization)
    if not test_state:
        return

    # 检查依赖 / Check dependencies
    skip_reason = None
    if test_type == 'interface' and not test_state.flash_test_passed:
        skip_reason = "Flash test has not passed yet. Skipping dependent tests. / 刷写测试未通过，跳过依赖测试。"
    elif test_type == 'function' and not test_state.interface_test_passed:
        skip_reason = "Interface test has not passed yet. Skipping dependent tests. / 接口测试未通过，跳过依赖测试。"
    elif test_type == 'performance' and not test_state.function_test_passed:
        skip_reason = "Function test has not passed yet. Skipping dependent tests. / 功能测试未通过，跳过依赖测试。"

    # 如果需要跳过，抛出SkipException / Skip if needed, raise SkipException
    if skip_reason:
        pytest.skip(skip_reason)
