"""
Pytest Configuration File / Pytest 配置文件
全局测试配置和fixture定义
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pytest

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# 全局报告生成器实例 / Global report generator instance
_excel_report_generator = None

# 存储当前测试item / Store current test item
_current_test_item = None

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

    Note: Uses mock client for testing without real server connection.
    The mock simulates real client behavior including timeout and reconnection.
    注意: 使用模拟客户端进行测试，无需真实服务器连接。模拟客户端模拟真实行为包括超时和重连。
    """
    from unittest.mock import Mock, MagicMock

    # Create a realistic mock client with timeout simulation
    # 创建逼真的模拟客户端，包含超时模拟
    client = MagicMock()

    # Set connection properties
    # 设置连接属性
    client.host = test_config.get('host', 'localhost')
    client.port = test_config.get('port', 8080)
    client.token = test_config.get('token', 'your-secure-token-here')
    client.timeout = test_config.get('server_timeout', 5.0)

    # Connection state tracking
    # 连接状态跟踪
    client._connected = True
    client._last_activity = time.time()
    client._idle_timeout = test_config.get('client_timeout', 10.0)  # seconds

    # Mock send method with activity tracking
    # 模拟send方法，带活动跟踪
    def mock_send(request):
        """Mock send that tracks activity and simulates timeout"""
        if not client._connected:
            return False
        client._last_activity = time.time()
        return True

    client.send = mock_send

    # Mock receive method with timeout simulation
    # 模拟receive方法，带超时模拟
    def mock_receive(timeout=None):
        """Mock receive that simulates timeout"""
        if timeout is None:
            timeout = test_config.get('server_timeout', 5.0)

        if not client._connected:
            raise ConnectionError("Client not connected")

        elapsed = time.time() - client._last_activity
        if elapsed > client._idle_timeout:
            client._connected = False
            raise TimeoutError(f"Connection timed out after {elapsed:.1f}s idle")

        client._last_activity = time.time()
        return {"status": "ok", "timestamp": time.time()}

    client.receive = mock_receive

    # Property for checking connection status
    # 检查连接状态的属性
    def get_connected():
        """Check if client is connected (simulates idle timeout)"""
        # Auto-disconnect if idle timeout exceeded
        if client._connected and (time.time() - client._last_activity > client._idle_timeout):
            client._connected = False
        return client._connected

    def set_connected(value):
        client._connected = value
        if value:
            client._last_activity = time.time()

    client.connected = property(get_connected, set_connected)

    # Simulate timeout/disconnection
    # 模拟超时/断连
    def simulate_timeout(idle_duration=None):
        """
        Simulate idle timeout / 模拟空闲超时

        This simulates a real-world scenario where:
        1. Client has been idle for a period (no activity)
        2. The connection timeout check detects this and disconnects

        In a real client, this happens when:
        - The last activity time is set
        - Periodically checking if (now - last_activity) > timeout
        - Auto-disconnecting if timeout exceeded

        Args:
            idle_duration: Custom idle duration in seconds (default: exceeds timeout)
            idle_duration: 自定义空闲时长（秒，默认：超过超时时间）
        """
        if idle_duration is None:
            idle_duration = client._idle_timeout + 1

        # Simulate idle duration by setting last_activity to past time
        # 模拟空闲时长：设置最后活动时间为过去时间
        # This represents: client was active at (now - idle_duration), then idle until now
        # 这代表：客户端在 (now - idle_duration) 时有活动，然后一直空闲到现在
        print(f"  → Simulating idle for {idle_duration:.1f}s (last activity was {idle_duration:.1f}s ago)")
        client._last_activity = time.time() - idle_duration

        # Manually trigger the timeout check (simulating what happens in real client)
        # 手动触发超时检查（模拟真实客户端中发生的情况）
        elapsed = time.time() - client._last_activity
        if elapsed > client._idle_timeout:
            # In a real client, this happens when checking connection status
            # 在真实客户端中，这发生在检查连接状态时
            print(f"  → Idle timeout detected: {elapsed:.1f}s > {client._idle_timeout}s, disconnecting...")
            client._connected = False
        else:
            print(f"  → Idle duration: {elapsed:.1f}s, still within timeout limit")

    client.simulate_timeout = simulate_timeout

    # Simulate reconnection
    # 模拟重连
    def reconnect():
        """Simulate reconnection attempt / 模拟重连尝试"""
        time.sleep(0.1)  # Simulate connection delay / 模拟连接延迟
        client._connected = True
        client._last_activity = time.time()

    client.reconnect = reconnect

    # Mock close method
    # 模拟close方法
    def mock_close():
        """Mock close method"""
        client._connected = False

    client.close = mock_close

    yield client


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

    print(f"\n{'='*70}")
    print(f"测试会话开始 / Test Session Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"报告配置 / Report Config: {config_path}")
    print(f"模板文件 / Template: {generator.config['template']}")
    print(f"{'='*70}")


def pytest_runtest_logreport(report):
    """
    自动收集每个测试的结果 / Automatically collect results for each test

    使用钩子自动收集测试结果，无需手动添加报告代码
    Use hooks to automatically collect test results without manual reporting code

    Args:
        report: Test report object / 测试报告对象
    """
    global _excel_report_generator, _current_test_item

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

        # Update test_state when test passes
        # 测试通过时更新test_state
        if report.passed:
            # Get session-scoped test_state fixture
            # 获取session范围的test_state fixture
            try:
                if hasattr(report, 'item'):
                    item = report.item
                    # Try to get test_state from session
                    # 尝试从session获取test_state
                    if hasattr(item, 'session'):
                        session = item.session
                        if not hasattr(session, '_test_state_cache'):
                            # Manually create test_state instance
                            # 手动创建test_state实例
                            session._test_state_cache = TestState()

                        test_state = session._test_state_cache

                        # Update test state based on test type
                        # 根据测试类型更新测试状态
                        if test_type == 'flash':
                            test_state.mark_flash_passed()
                        elif test_type == 'interface':
                            test_state.mark_interface_passed()
                        elif test_type == 'function':
                            test_state.mark_function_passed()

            except Exception:
                # If we can't update test_state, continue anyway
                # 如果无法更新test_state，继续执行
                pass


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
    global _excel_report_generator
    generator = _excel_report_generator
    session_start_time = getattr(session.config, 'session_start_time', None)

    if generator and session_start_time:
        generator.stop()

        # 生成带时间戳的报告文件名 / Generate timestamped report filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_report_{timestamp}.xlsx"

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
    - 接口测试 (interface) → 依赖刷写测试完成 (test_flash_complete)
    - 功能测试 (function) → 依赖接口测试完成 (test_interface_complete)
    - 性能测试 (performance) → 依赖功能测试完成 (test_function_complete)

    Args:
        config: Pytest configuration / Pytest配置
        items: List of collected test items / 收集的测试项列表
    """
    # ==================== 第一步：过滤辅助函数 / Step 1: Filter out helper functions ====================
    # filtered_items = []
    # for item in items:
    #     # 检查是否是辅助函数（名称包含 _test_ 且在 common.py 中）
    #     # Check if it's a helper function (name contains _test_ and is in common.py)
    #     if "_test_" in item.name and "common.py" in str(item.fspath):
    #         continue  # 跳过辅助函数 / Skip helper function
    #     filtered_items.append(item)
    # items[:] = filtered_items

    # ==================== 第二步：添加依赖标记 / Step 2: Add dependency markers ====================
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

    # 禁用自动添加pytest-dependency标记，因为pytest_runtest_setup已经基于test_state实现了依赖检查
    # Disable automatic pytest-dependency marker addition, as pytest_runtest_setup already implements
    # dependency checking based on test_state
    # for item in items:
    #     # 检查测试类型标记 / Check test type markers
    #     for marker_name in ['interface', 'function', 'performance']:
    #         if item.get_closest_marker(marker_name):
    #             # 添加自动依赖标记 / Add automatic dependency marker
    #             dependency_name = dependency_mapping.get(marker_name)
    #             if dependency_name:
    #                 # 使用pytest-dependency的内部API添加依赖
    #                 # Use pytest-dependency's internal API to add dependency
    #                 item.add_marker(
    #                     pytest.mark.dependency(
    #                         depends=[dependency_name],
    #                         name=f"{marker_name}_auto_dep_{item.name}"
    #                     )
    #                 )
    #                 # 打印调试信息 / Print debug info
    #                 print(f"[Auto Dependency] {item.name} → depends on {dependency_name}")
    #             break

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
    global _current_test_item
    _current_test_item = item  # 存储当前item / Store current item

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
        # Try to get from session cache first
        # 首先尝试从session缓存获取
        if hasattr(item, 'session'):
            session = item.session
            test_state = getattr(session, '_test_state_cache', None)

        # If not in cache, try to get from fixture manager
        # 如果不在缓存中，尝试从fixture管理器获取
        if not test_state:
            # 使用pytest的fixture管理器 / Use pytest's fixture manager
            if hasattr(item, '_fixtureinfo'):
                fixturedef = item._fixtureinfo.name2fixturedefs.get('test_state')
                if fixturedef:
                    test_state = fixturedef[0].cached_result
                    if test_state:
                        test_state = test_state[0]  # 获取fixture的返回值 / Get fixture return value
                        # Cache it to session for future access
                        # 缓存到session以便未来访问
                        if hasattr(item, 'session'):
                            item.session._test_state_cache = test_state
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
