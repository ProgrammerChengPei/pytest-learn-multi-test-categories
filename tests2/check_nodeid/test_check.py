"""
检查 pytest-dependency 实际使用的 nodeid 格式
"""
import pytest


@pytest.fixture(autouse=True)
def print_nodeid(request):
    """自动打印 nodeid"""
    print(f"\n[CHECK] nodeid: {request.node.nodeid}")
    print(f"[CHECK] fspath: {request.node.fspath}")
    print(f"[CHECK] name: {request.node.name}")


class TestCheck:
    def test_a(self):
        """Test A"""
        assert True

    @pytest.mark.dependency(depends=["test_a"])
    def test_b(self):
        """Test B depends on A"""
        assert True
