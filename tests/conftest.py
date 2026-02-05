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


class MockClient:
    """
    Mock client for testing / 测试用模拟客户端

    Simulates real client behavior including connection management,
    timeout handling, and activity tracking.
    模拟真实客户端行为，包括连接管理、超时处理和活动跟踪。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mock client / 初始化模拟客户端

        Args:
            config: Test configuration dictionary / 测试配置字典
        """
        # Connection properties / 连接属性
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8080)
        self.token = config.get('token', 'your-secure-token-here')
        self.timeout = config.get('server_timeout', 5.0)

        # Connection state / 连接状态
        self._connected = True
        self._last_activity = time.time()
        self._idle_timeout = config.get('client_timeout', 10.0)

        # Response simulation / 响应模拟
        self._mock_responses: Dict[str, Any] = {
            'get_status': {'type': 'response', 'status': 'ok', 'server_time': time.time(), 'connections': 1},
            'health_check': {'type': 'response', 'status': 'healthy'},
            'echo_with_timestamp': lambda req: self._create_echo_response(req)
        }

        # Request ID counter / 请求ID计数器
        self._request_id = 0

    def send(self, request: Dict[str, Any]) -> bool:
        """
        Send request and track activity / 发送请求并跟踪活动

        Args:
            request: Request dictionary / 请求字典

        Returns:
            True if send was successful / 发送成功返回True
        """
        if not self._connected:
            return False
        self._last_activity = time.time()
        return True

    def _create_echo_response(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create echo response for echo_with_timestamp command / 创建echo响应"""
        return {
            'type': 'response',
            'id': request.get('id', self._increment_request_id()),
            'status': 'ok',
            'original_text': request.get('text', ''),
            'server_response': 'Echo: ' + request.get('text', ''),
            'server_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def _increment_request_id(self) -> int:
        """Increment and return request ID / 增加并返回请求ID"""
        self._request_id += 1
        return self._request_id

    def get_mock_response(self, command: str, request: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get mock response for a command / 获取命令的模拟响应

        Args:
            command: Command name / 命令名称
            request: Original request (for lambda responses) / 原始请求（用于lambda响应）

        Returns:
            Mock response dictionary with id field / 包含id字段的模拟响应字典
        """
        response = self._mock_responses.get(command, {})
        if callable(response):
            return response(request)

        # Add id field to static responses
        if isinstance(response, dict) and 'id' not in response:
            response = response.copy()
            response['id'] = self._increment_request_id()

        return response

    def receive(self, timeout: float = None) -> Dict[str, Any]:
        """
        Receive response with timeout check / 接收响应并检查超时

        Note: This is kept for API compatibility, but actual responses
        are generated via get_mock_response in test helpers.
        注意: 保留此方法用于API兼容，但实际响应通过测试辅助函数中的get_mock_response生成。

        Args:
            timeout: Timeout in seconds / 超时时间(秒)

        Returns:
            Response dictionary / 响应字典

        Raises:
            ConnectionError: If client is not connected / 如果客户端未连接
            TimeoutError: If idle timeout exceeded / 如果超过空闲超时
        """
        if not self._connected:
            raise ConnectionError("Client not connected")

        elapsed = time.time() - self._last_activity
        if elapsed > self._idle_timeout:
            self._connected = False
            raise TimeoutError(f"Connection timed out after {elapsed:.1f}s idle")

        self._last_activity = time.time()
        return {"status": "ok", "timestamp": time.time()}

    def simulate_timeout(self, idle_duration: float = None) -> None:
        """
        Simulate idle timeout / 模拟空闲超时

        Args:
            idle_duration: Idle duration in seconds (default: exceeds timeout)
            idle_duration: 空闲时长（秒，默认：超过超时时间）
        """
        if idle_duration is None:
            idle_duration = self._idle_timeout + 1

        self._last_activity = time.time() - idle_duration
        elapsed = time.time() - self._last_activity

        if elapsed > self._idle_timeout:
            print(f"  → Idle timeout detected: {elapsed:.1f}s > {self._idle_timeout}s")
            self._connected = False
        else:
            print(f"  → Idle duration: {elapsed:.1f}s, within limit")

    def reconnect(self) -> None:
        """Simulate reconnection / 模拟重连"""
        time.sleep(0.1)
        self._connected = True
        self._last_activity = time.time()

    def close(self) -> None:
        """Close connection / 关闭连接"""
        self._connected = False

    @property
    def connected(self) -> bool:
        """
        Check if client is connected / 检查客户端是否已连接

        Auto-disconnects if idle timeout exceeded.
        如果超过空闲超时时间则自动断连。
        """
        if self._connected and (time.time() - self._last_activity > self._idle_timeout):
            self._connected = False
        return self._connected

    @connected.setter
    def connected(self, value: bool) -> None:
        """Set connection status / 设置连接状态"""
        self._connected = value
        if value:
            self._last_activity = time.time()


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
