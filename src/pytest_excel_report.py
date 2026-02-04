"""
Pytest Plugin for Excel Report Generation / 用于生成Excel报告的Pytest插件
"""
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest


class ExcelReportPlugin:
    """
    Pytest plugin to collect test results and generate Excel reports
    收集测试结果并生成Excel报告的Pytest插件
    """

    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.start_time: float = 0
        self.end_time: float = 0
        self.artifacts_dir: Path = None

    def pytest_configure(self, config):
        """Configure hook / 配置钩子"""
        self.artifacts_dir = Path(config.rootdir) / "test_artifacts"
        self.artifacts_dir.mkdir(exist_ok=True)

        # Register markers / 注册标记
        config.addinivalue_line("markers", "flash: Flash/Firmware tests")
        config.addinivalue_line("markers", "interface: Interface tests")
        config.addinivalue_line("markers", "function: Function tests")
        config.addinivalue_line("markers", "performance: Performance tests")

    def pytest_sessionstart(self, session):
        """Session start hook / 会话开始钩子"""
        self.start_time = time.time()
        print("\n" + "="*60)
        print("Starting Pytest Test Session / 开始Pytest测试会话")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")

    def pytest_sessionfinish(self, session, exitstatus):
        """Session finish hook / 会话结束钩子"""
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        print("\n" + "="*60)
        print("Pytest Session Finished / Pytest会话结束")
        print(f"Duration: {duration:.2f} seconds / 耗时: {duration:.2f}秒")
        print(f"Exit Status: {exitstatus}")
        print("="*60 + "\n")

        # Generate Excel report / 生成Excel报告
        self._generate_excel_report()

    def pytest_runtest_logreport(self, report):
        """
        Collect test result / 收集测试结果

        Args:
            report: Test report object / 测试报告对象
        """
        if report.when == 'call':
            # Determine test category / 确定测试类别
            category = self._get_test_category(report)

            result = {
                'name': report.nodeid,
                'category': category,
                'status': report.outcome,
                'duration': report.duration,
                'message': self._get_failure_message(report) if report.failed else 'Test passed'
            }

            self.test_results.append(result)

    def _get_test_category(self, report) -> str:
        """
        Get test category from markers / 从标记获取测试类别

        Args:
            report: Test report object / 测试报告对象

        Returns:
            Test category string / 测试类别字符串
        """
        item = pytest.Item.from_parent(report.node, parent=report.node.parent)

        if report.node.get_closest_marker('flash'):
            return 'flash'
        elif report.node.get_closest_marker('interface'):
            return 'interface'
        elif report.node.get_closest_marker('function'):
            return 'function'
        elif report.node.get_closest_marker('performance'):
            return 'performance'
        else:
            return 'other'

    def _get_failure_message(self, report) -> str:
        """
        Get failure message from report / 从报告获取失败消息

        Args:
            report: Test report object / 测试报告对象

        Returns:
            Failure message string / 失败消息字符串
        """
        if hasattr(report, 'longrepr'):
            longrepr = report.longrepr
            if longrepr:
                return str(longrepr)
        return "Test failed"

    def _generate_excel_report(self):
        """Generate Excel report / 生成Excel报告"""
        try:
            from excel_report import ExcelReportGenerator

            generator = ExcelReportGenerator(self.artifacts_dir)
            generator.start_time = self.start_time
            generator.end_time = self.end_time

            for result in self.test_results:
                generator.add_test_result(result)

            generator.generate_report("pytest_report.xlsx")

        except ImportError:
            print("Warning: openpyxl not installed. Skipping Excel report generation.")
            print("Install with: pip install openpyxl")
        except Exception as e:
            print(f"Error generating Excel report: {e}")


@pytest.fixture
def excel_report():
    """
    Fixture to access Excel report generator / 访问Excel报告生成器的fixture

    Returns:
        Excel report generator instance / Excel报告生成器实例
    """
    from excel_report import ExcelReportGenerator

    return ExcelReportGenerator(Path("test_artifacts"))


# Register plugin / 注册插件
def pytest_configure(config):
    """Register the plugin / 注册插件"""
    config.pluginmanager.register(ExcelReportPlugin(), 'excel_report_plugin')
    config.pluginmanager.register(ExcelReportPlugin(), 'excel_report_plugin')
