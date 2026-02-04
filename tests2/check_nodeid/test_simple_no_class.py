"""
无类的简单测试，检查 pytest-dependency
"""
import pytest


@pytest.mark.dependency(name="simple_test_no_class_a")
def test_no_class_a():
    """Test A without class"""
    print("✓ test_no_class_a")
    assert True


@pytest.mark.dependency(depends=["simple_test_no_class_a"])
def test_no_class_b():
    """Test B depends on A"""
    print("✓ test_no_class_b")
    assert True
