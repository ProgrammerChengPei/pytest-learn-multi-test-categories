"""
Simple test to verify pytest-dependency behavior
"""
import pytest


class TestSimple:
    """Simple test class"""

    @pytest.mark.dependency(name="test_a")
    def test_a(self):
        """Test A"""
        print("✓ test_a")
        assert True

    @pytest.mark.dependency(depends=["test_a"])
    def test_b(self):
        """Test B depends on A"""
        print("✓ test_b")
        assert True
