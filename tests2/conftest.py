"""
Pytest Configuration File / Pytest 配置文件
测试验证 conftest - 使用全名 nodeid + tryfirst=True
"""
import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """
    测试排序 hook，设置为最早执行
    
    确保 pytest-dependency 在我们的排序之后再注册依赖关系
    """
    # 定义测试顺序
    phase_order = {
        'flash': 0,
        'interface': 1,
        'function': 2,
        'performance': 3
    }

    def get_test_order(item):
        """获取测试顺序"""
        for marker_name, order in phase_order.items():
            if item.get_closest_marker(marker_name):
                return order
        return 99

    items.sort(key=get_test_order)
    print(f"\n[验证] 测试排序完成，共 {len(items)} 个测试项")
    for i, item in enumerate(items):
        print(f"  {i+1}. {item.nodeid}")
