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
from datetime import datetime

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
# 自动Excel报告生成钩子 / Automatic Excel Report Generation Hooks
# ============================================================================

def pytest_sessionstart(session):
    """
    测试会话开始时初始化报告生成器 / Initialize report generator at session start

    使用钩子自动初始化Excel报告生成器，无需手动调用
    Use hooks to automatically initialize Excel report generator without manual calls

    Args:
        session: Pytest session object / Pytest会话对象
    """
    from src.excel_report import ExcelReportGenerator

    # 创建报告输出目录 / Create report output directory
    output_dir = project_root / "reports"
    output_dir.mkdir(exist_ok=True)

    # 初始化报告生成器并存储在session中 / Initialize report generator and store in session
    generator = ExcelReportGenerator(output_dir)
    generator.start()

    # 存储到session对象中 / Store to session object
    session.config.excel_report_generator = generator
    session.config.session_start_time = time.time()

    print(f"\n{'='*70}")
    print(f"测试会话开始 / Test Session Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")


def pytest_runtest_logreport(report):
    """
    自动收集每个测试的结果 / Automatically collect results for each test

    使用钩子自动收集测试结果，无需手动添加报告代码
    Use hooks to automatically collect test results without manual reporting code

    Args:
        report: Test report object / 测试报告对象
    """
    # 只在测试完成时收集结果 / Collect results only when test is complete
    if report.when == 'call':
        generator = report.session.config.excel_report_generator

        # 从测试节点获取测试类别 / Get test category from test node
        test_node = report.node
        test_type = None
        for marker_name in ['flash', 'interface', 'function', 'performance']:
            if test_node.get_closest_marker(marker_name):
                test_type = marker_name
                break

        if test_type:
            # 构建测试结果字典 / Build test result dictionary
            test_result = {
                'name': report.node.name,
                'category': test_type,
                'status': 'passed' if report.passed else 'failed' if report.failed else 'skipped',
                'duration': report.duration,
                'message': str(report.longrepr) if not report.passed else '',
                'file': str(test_node.fspath),
                'line': test_node.lineno
            }

            # 性能测试额外信息 / Performance test additional info
            if test_type == 'performance':
                # 尝试从report中提取性能指标 / Try to extract performance metrics from report
                if hasattr(report, 'user_properties'):
                    for key, value in report.user_properties:
                        if key == 'metric':
                            test_result['metric'] = value
                        elif key == 'value':
                            test_result['value'] = value

            # 添加到报告生成器 / Add to report generator
            generator.add_test_result(test_result)

            # 打印测试结果摘要 / Print test result summary
            status_icon = "✓" if report.passed else "✗" if report.failed else "⊘"
            print(f"  [{status_icon}] {test_type.upper()}: {report.node.name} - {test_result['status']} ({report.duration:.3f}s)")


def pytest_runtest_makereport(item, call):
    """
    自动标记测试完成状态 / Automatically mark test completion status

    使用钩子自动更新测试状态管理器，无需手动调用mark_*_passed()
    Use hooks to automatically update test state manager without manual mark_*_passed() calls

    Args:
        item: Test item / 测试项
        call: Test call object / 测试调用对象

    Returns:
        Modified report / 修改后的报告
    """
    report = call.result if call else None

    if report and report.when == 'call' and report.passed:
        test_state = None

        # 获取test_state fixture / Get test_state fixture
        try:
            if hasattr(item, '_fixtureinfo'):
                fixturedef = item._fixtureinfo.name2fixturedefs.get('test_state')
                if fixturedef:
                    test_state = fixturedef[0].cached_result
                    if test_state:
                        test_state = test_state[0]
        except Exception:
            pass

        # 自动更新测试完成状态 / Automatically update test completion status
        if test_state:
            if item.get_closest_marker('flash'):
                test_state.mark_flash_passed()
            elif item.get_closest_marker('interface'):
                test_state.mark_interface_passed()
            elif item.get_closest_marker('function'):
                test_state.mark_function_passed()

    return report


def pytest_sessionfinish(session, exitstatus):
    """
    测试会话结束时自动生成报告 / Automatically generate report at session end

    使用钩子自动生成Excel报告，无需手动调用
    Use hooks to automatically generate Excel report without manual calls

    Args:
        session: Pytest session object / Pytest会话对象
        exitstatus: Exit status code / 退出状态码
    """
    generator = getattr(session.config, 'excel_report_generator', None)
    session_start_time = getattr(session.config, 'session_start_time', None)

    if generator and session_start_time:
        generator.stop()

        # 生成带时间戳的报告文件名 / Generate timestamped report filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_report_{timestamp}.xlsx"

        print(f"\n{'='*70}")
        print(f"生成测试报告 / Generating Test Report...")
        print(f"{'='*70}")

        # 生成报告 / Generate report
        report_path = generator.generate_report(filename)

        # 打印统计信息 / Print statistics
        total_tests = len(generator.test_results)
        passed_tests = len([r for r in generator.test_results if r.get('status') == 'passed'])
        failed_tests = len([r for r in generator.test_results if r.get('status') == 'failed'])
        skipped_tests = len([r for r in generator.test_results if r.get('status') == 'skipped'])

        print(f"\n测试统计 / Test Statistics:")
        print(f"  总数 / Total:     {total_tests}")
        print(f"  通过 / Passed:    {passed_tests} ({passed_tests/total_tests*100:.1f}%)" if total_tests > 0 else f"  通过 / Passed:    {passed_tests}")
        print(f"  失败 / Failed:    {failed_tests} ({failed_tests/total_tests*100:.1f}%)" if total_tests > 0 else f"  失败 / Failed:    {failed_tests}")
        print(f"  跳过 / Skipped:   {skipped_tests}")
        print(f"  耗时 / Duration:  {generator.end_time - session_start_time:.2f}s")
        print(f"\n报告路径 / Report Path: {report_path}")
        print(f"{'='*70}\n")


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
