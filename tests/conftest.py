"""
Pytest Configuration File / Pytest 配置文件
全局测试配置和fixture定义
"""
import json5
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from tests.comm.mock_client import MockClient
from tests.comm.wireshark import WiresharkManager

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# 全局报告生成器实例 / Global report generator instance
_excel_report_generator = None

# 存储当前测试item / Store current test item
_current_test_item = None

# 全局 Wireshark 管理器 / Global Wireshark manager
_wireshark_manager: Optional['WiresharkManager'] = None

@pytest.fixture(scope="function", autouse=True)
def ensure_client_connected(test_client):
    """
    Auto-ensure client is connected before each test / 每个测试前自动确保客户端已连接

    Checks if client is disconnected (e.g., due to timeout) and reconnects if needed.
    Uses real timeout simulation with time.sleep.
    检查客户端是否断连（如超时导致），必要时重新连接。使用time.sleep模拟真实超时。
    """
    # Check if client is disconnected due to timeout and reconnect if needed
    # 检查客户端是否因超时断连，必要时重新连接
    if not test_client.connected:
        print("  → Client disconnected, reconnecting...")
        test_client.reconnect()

    yield



@pytest.fixture(scope="function")
def test_client(test_config):
    """
    Create test client instance / 创建测试客户端实例

    Note: Uses MockClient for testing without real server connection.
    注意: 使用 MockClient 进行测试，无需真实服务器连接。
    """
    client = MockClient(test_config)
    yield client


# 全局测试状态存储
class TestState:
    """Test state manager / 测试状态管理器"""
    def __init__(self):
        self.flash_test_total = 0
        self.flash_test_passed_count = 0
        self.flash_test_failed = False
        self.interface_test_total = 0
        self.interface_test_passed_count = 0
        self.interface_test_failed = False
        self.function_test_total = 0
        self.function_test_passed_count = 0
        self.function_test_failed = False
        self.results: Dict[str, Any] = {}

    def set_flash_total(self, count: int):
        """设置 flash 测试总数 / Set total flash tests count"""
        self.flash_test_total = count

    def increment_flash_passed(self):
        """增加 flash 测试通过计数 / Increment flash tests passed count"""
        self.flash_test_passed_count += 1

    def mark_flash_failed(self):
        """标记 flash 测试失败 / Mark flash test failed"""
        self.flash_test_failed = True

    def is_flash_complete(self) -> bool:
        """检查 flash 测试是否全部通过 / Check if all flash tests passed"""
        return (self.flash_test_passed_count == self.flash_test_total
                and self.flash_test_total > 0
                and not self.flash_test_failed)

    def set_interface_total(self, count: int):
        """设置 interface 测试总数 / Set total interface tests count"""
        self.interface_test_total = count

    def increment_interface_passed(self):
        """增加 interface 测试通过计数 / Increment interface tests passed count"""
        self.interface_test_passed_count += 1

    def mark_interface_failed(self):
        """标记 interface 测试失败 / Mark interface test failed"""
        self.interface_test_failed = True

    def is_interface_complete(self) -> bool:
        """检查 interface 测试是否全部通过 / Check if all interface tests passed"""
        return (self.interface_test_passed_count == self.interface_test_total
                and self.interface_test_total > 0
                and not self.interface_test_failed)

    def set_function_total(self, count: int):
        """设置 function 测试总数 / Set total function tests count"""
        self.function_test_total = count

    def increment_function_passed(self):
        """增加 function 测试通过计数 / Increment function tests passed count"""
        self.function_test_passed_count += 1

    def mark_function_failed(self):
        """标记 function 测试失败 / Mark function test failed"""
        self.function_test_failed = True

    def is_function_complete(self) -> bool:
        """检查 function 测试是否全部通过 / Check if all function tests passed"""
        return (self.function_test_passed_count == self.function_test_total
                and self.function_test_total > 0
                and not self.function_test_failed)

    # 保留旧方法以兼容 / Keep old methods for compatibility
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
        return json5.load(f)


@pytest.fixture(scope="session")
def reports_dir():
    """Create and return reports directory / 创建并返回测试报告目录"""
    artifacts_dir = project_root / "reports"
    artifacts_dir.mkdir(exist_ok=True)
    return artifacts_dir


@pytest.fixture
def temp_file(reports_dir):
    """Create a temporary file for testing / 创建临时测试文件"""
    def _create_temp_file(name: str, content: str = ""):
        temp_path = reports_dir / name
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return temp_path

    return _create_temp_file

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
    config.addinivalue_line("markers", "chinese_name: Chinese name for test case / 测试用例中文名")
    config.addinivalue_line("markers", "private: Private helper function / 私有辅助函数")



# ============================================================================
# 自动Excel报告生成钩子 / Automatic Excel Report Generation Hooks
# ============================================================================

def pytest_sessionstart(session):
    """
    测试会话开始时初始化报告生成器 / Initialize report generator at session start

    使用基于模板的Excel报告生成器，通过JSON配置映射数据到模板
    Use template-based Excel report generator with JSON config for data mapping

    Args:
        session: Pytest session object / Pytest会话对象
    """
    global _excel_report_generator
    from tests.common.template_based_report import TemplateBasedReportGenerator

    # 报告配置文件路径 / Report config file path
    config_path = project_root / "configs" / "report_config.json"

    # 初始化基于模板的报告生成器 / Initialize template-based report generator
    generator = TemplateBasedReportGenerator(config_path)
    generator.start()

    # 存储到全局变量和session对象中 / Store to global variable and session object
    global _excel_report_generator
    _excel_report_generator = generator
    session.config.session_start_time = time.time()

    # 初始化 test_state 并存储到 session
    # Initialize test_state and store to session
    from tests.conftest import TestState
    session._test_state_cache = TestState()

    print(f"\n{'='*70}")
    print(f"测试会话开始 / Test Session Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"报告配置 / Report Config: {config_path}")
    print(f"模板文件 / Template: {generator.config['template']}")

    # 初始化 Wireshark 管理器 / Initialize Wireshark manager
    global _wireshark_manager
    test_config_path = project_root / "configs" / "config.json"
    with open(test_config_path, 'r', encoding='utf-8') as f:
        test_config = json5.load(f)

    reports_dir = project_root / "reports"
    _wireshark_manager = WiresharkManager(test_config, reports_dir)

    wireshark_status = "enabled" if _wireshark_manager.enabled else "disabled"
    print(f"Wireshark抓包 / Packet Capture: {wireshark_status}")
    print(f"{'='*70}")


def pytest_runtest_logreport(report):
    """
    自动收集每个测试的结果 / Automatically collect results for each test

    使用钩子自动收集测试结果，无需手动添加报告代码
    Use hooks to automatically collect test results without manual reporting code

    Args:
        report: Test report object / 测试报告对象
    """
    global _excel_report_generator, _current_test_item, _wireshark_manager

    # 测试完成时停止抓包 / Stop capture when test is complete
    if report.when == 'call' and _wireshark_manager and _wireshark_manager.enabled:
        capture_file = _wireshark_manager.stop_capture()
        if capture_file:
            print(f"  [Wireshark] Capture saved: {capture_file.name}")

    # 只在测试完成时收集结果 / Collect results only when test is complete
    if report.when == 'call':
        generator = _excel_report_generator
        if not generator:
            return  # 没有初始化报告生成器，跳过 / No report generator initialized, skip

        # 从全局变量获取item / Get item from global variable
        test_node = _current_test_item
        if not test_node:
            return

        # 从测试节点获取测试类别 / Get test category from test node
        test_type = None
        for marker_name in ['flash', 'interface', 'function', 'performance']:
            if test_node.get_closest_marker(marker_name):
                test_type = marker_name
                break

        if test_type:
            # 提取docstring用于报告 / Extract docstring for reporting
            docstring = ''
            if test_node.obj and test_node.obj.__doc__:
                docstring = test_node.obj.__doc__.strip()

            # 构建测试结果字典 / Build test result dictionary
            test_result = {
                'name': report.nodeid.split('::')[-1],
                'category': test_type,
                'status': 'passed' if report.passed else 'failed' if report.failed else 'skipped',
                'duration': report.duration,
                'message': str(report.longrepr) if not report.passed else docstring,
                'file': str(test_node.fspath),
                'line': getattr(test_node, 'lineno', 0) or 0
            }

            # 提取测试用例中文名 / Extract Chinese name from test case
            chinese_name = None
            # 尝试从自定义marker中获取中文名 / Try to get Chinese name from custom marker
            chinese_name_marker = test_node.get_closest_marker('chinese_name')
            if chinese_name_marker:
                chinese_name = chinese_name_marker.args[0] if chinese_name_marker.args else None

            # 如果没有marker，尝试从文档字符串提取 / Try to extract from docstring if no marker
            if not chinese_name:
                if docstring:
                    # 检查文档字符串第一行是否是中文 / Check if first line of docstring is Chinese
                    # 简单的判断：如果不是英文开头，可能是中文
                    if any('\u4e00' <= c <= '\u9fff' for c in docstring[:20]):
                        # 取第一行作为中文名 / Take first line as Chinese name
                        chinese_name = docstring.split('\n')[0].strip()

            # 如果找到了中文名，添加到测试结果 / Add to test result if Chinese name found
            if chinese_name:
                test_result['chinese_name'] = chinese_name

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
            name_display = chinese_name if chinese_name else test_result['name']
            print(f"  [{status_icon}] {test_type.upper()}: {name_display} ({report.duration:.3f}s)")

            # Update test_state when test completes (passed or failed)
            # 测试完成时更新test_state（通过或失败）
            try:
                if hasattr(report, 'item'):
                    item = report.item
                    if hasattr(item, 'session'):
                        session = item.session
                        test_state = getattr(session, '_test_state_cache', None)

                        if test_state:
                            # 根据测试类型更新测试状态 / Update test state based on test type
                            if test_type == 'flash':
                                if report.passed:
                                    test_state.increment_flash_passed()
                                elif report.failed:
                                    test_state.mark_flash_failed()
                            elif test_type == 'interface':
                                if report.passed:
                                    test_state.increment_interface_passed()
                                elif report.failed:
                                    test_state.mark_interface_failed()
                            elif test_type == 'function':
                                if report.passed:
                                    test_state.increment_function_passed()
                                elif report.failed:
                                    test_state.mark_function_failed()

            except Exception:
                pass  # 如果无法更新test_state，继续执行 / If can't update test_state, continue


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
    # 检查call是否有结果 / Check if call has result
    if not call or not hasattr(call, 'result') or call.when != 'call':
        return None

    try:
        report = call.result
        if not report:
            return None
    except AttributeError:
        # call没有有效结果（例如测试失败时） / call has no valid result (e.g., when test fails)
        return None

    if report.passed:
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
    global _excel_report_generator, _wireshark_manager
    generator = _excel_report_generator
    session_start_time = getattr(session.config, 'session_start_time', None)

    # 清理 Wireshark 资源 / Cleanup Wireshark resources
    if _wireshark_manager:
        _wireshark_manager.cleanup()

    if generator and session_start_time:
        generator.stop()

        # 生成带时间戳的报告文件名 / Generate timestamped report filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # filename = f"test_report_{timestamp}.xlsx"
        filename = f"test_report.xlsx"

        print(f"\n{'='*70}")
        print("生成测试报告 / Generating Test Report...")
        print(f"{'='*70}")

        # 生成报告 / Generate report
        report_path = generator.generate_report(filename)

        # 打印统计信息 / Print statistics
        total_tests = len(generator.test_results)
        passed_tests = len([r for r in generator.test_results if r.get('status') == 'passed'])
        failed_tests = len([r for r in generator.test_results if r.get('status') == 'failed'])
        skipped_tests = len([r for r in generator.test_results if r.get('status') == 'skipped'])

        print("\n测试统计 / Test Statistics:")
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
    自动添加测试依赖标记并过滤辅助函数 / Automatically add test dependency markers and filter out helper functions

    使用钩子自动管理测试依赖，避免在每个测试上手动添加装饰器
    Use hooks to automatically manage test dependencies, avoiding manual decorators

    依赖规则 / Dependency Rules:
    - 接口测试 (interface) → 依赖所有刷写测试完成 (all flash tests passed)
    - 功能测试 (function) → 依赖所有接口测试完成 (all interface tests passed)
    - 性能测试 (performance) → 依赖所有功能测试完成 (all function tests passed)

    Args:
        config: Pytest configuration / Pytest配置
        items: List of collected test items / 收集的测试项列表
    """
    # ==================== 第一步：统计各类测试数量 / Step 1: Count tests by category ====================
    flash_count = sum(1 for item in items if item.get_closest_marker('flash'))
    interface_count = sum(1 for item in items if item.get_closest_marker('interface'))
    function_count = sum(1 for item in items if item.get_closest_marker('function'))

    # 存储到 session 中供后续使用 / Store to session for later use
    config._flash_test_total = flash_count
    config._interface_test_total = interface_count
    config._function_test_total = function_count

    # ==================== 第二步：注册依赖名称 / Step 2: Register dependency names ====================
    # 首先注册所有已命名测试到pytest-dependency系统
    # First register all named tests to pytest-dependency system
    for item in items:
        # 获取测试的dependency name（如果已设置）
        # Get test's dependency name (if set)
        dependency_marker = item.get_closest_marker('dependency')
        if dependency_marker and 'name' in dependency_marker.kwargs:
            dep_name = dependency_marker.kwargs['name']
            # 将简化名称存储为别名，使pytest-dependency能找到它
            # Store simplified name as alias so pytest-dependency can find it
            setattr(item, '_dep_name', dep_name)
            # 同时将简化名称也注册到item的属性中
            # Also register simplified name to item's attributes
            item._dependency_names = getattr(item, '_dependency_names', [])
            item._dependency_names.append(dep_name)

    # 按测试类型排序 / Sort by test type
    phase_order = {
        'flash': 0,
        'interface': 1,
        'function': 2,
        'performance': 3
    }

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
    global _current_test_item, _wireshark_manager
    _current_test_item = item  # 存储当前item / Store current item

    # 启动 Wireshark 抓包 / Start Wireshark capture
    if _wireshark_manager and _wireshark_manager.enabled:
        test_name = item.name.replace('::', '_').replace('[', '_').replace(']', '')
        _wireshark_manager.start_capture(test_name)

    # 检查测试类型 / Check test type
    test_type = None
    for marker in ['interface', 'function', 'performance']:
        if item.get_closest_marker(marker):
            test_type = marker
            break

    if not test_type:
        return  # 不是需要依赖检查的测试 / Not a test requiring dependency check

    # 获取test_state / Get test_state
    test_state = None
    try:
        if hasattr(item, 'session'):
            session = item.session
            test_state = getattr(session, '_test_state_cache', None)

            # 初始化测试计数（第一次运行该类型测试时）
            # Initialize test counts (first time running this type of test)
            if test_state and hasattr(session.config, '_flash_test_total'):
                if test_type == 'interface' and test_state.flash_test_total == 0:
                    test_state.set_flash_total(session.config._flash_test_total)
                elif test_type == 'function' and test_state.interface_test_total == 0:
                    test_state.set_interface_total(session.config._interface_test_total)
                elif test_type == 'performance' and test_state.function_test_total == 0:
                    test_state.set_function_total(session.config._function_test_total)
    except Exception:
        pass

    # 如果无法获取test_state，跳过检查 / If can't get test_state, skip check
    if not test_state:
        return

    # 检查依赖 / Check dependencies
    skip_reason = None
    if test_type == 'interface':
        if not test_state.is_flash_complete():
            passed = test_state.flash_test_passed_count
            total = test_state.flash_test_total
            skip_reason = f"Flash tests not all passed ({passed}/{total}). Skipping interface tests. / 刷写测试未全部通过（{passed}/{total}），跳过接口测试。"
    elif test_type == 'function':
        if not test_state.is_interface_complete():
            passed = test_state.interface_test_passed_count
            total = test_state.interface_test_total
            skip_reason = f"Interface tests not all passed ({passed}/{total}). Skipping function tests. / 接口测试未全部通过（{passed}/{total}），跳过功能测试。"
    elif test_type == 'performance':
        if not test_state.is_function_complete():
            passed = test_state.function_test_passed_count
            total = test_state.function_test_total
            skip_reason = f"Function tests not all passed ({passed}/{total}). Skipping performance tests. / 功能测试未全部通过（{passed}/{total}），跳过性能测试。"

    # 如果需要跳过，抛出SkipException / Skip if needed, raise SkipException
    if skip_reason:
        pytest.skip(skip_reason)
