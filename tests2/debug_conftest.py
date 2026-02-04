"""
Debug conftest for pytest-dependency analysis
"""
import pytest


@pytest.fixture(autouse=True)
def debug_dependency_check(request):
    """在每个测试执行前调试依赖检查"""
    marker = request.node.get_closest_marker('dependency')
    if marker:
        print(f"\n[DEBUG] 测试: {request.node.nodeid}")
        print(f"[DEBUG] dependency marker kwargs: {marker.kwargs}")
        
        if 'depends' in marker.kwargs:
            for dep_name in marker.kwargs['depends']:
                print(f"[DEBUG] 检查依赖: {dep_name}")


def pytest_runtest_logreport(report):
    """调试测试报告"""
    if report.when == 'setup':
        item = report.nodeid
        if hasattr(report, 'wasxfail'):
            print(f"[DEBUG] {item} - setup: {report.outcome}")
