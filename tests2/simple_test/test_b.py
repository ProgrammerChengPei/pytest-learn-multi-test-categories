"""
Test B file - depends on Test A
"""
import pytest


@pytest.mark.dependency(depends=["test_cross_a"])
def test_cross_b():
    """Test B depends on A"""
    print("✓ test_cross_b")
    assert True
