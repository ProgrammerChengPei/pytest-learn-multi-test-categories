"""
Test A file
"""
import pytest


@pytest.mark.dependency(name="test_cross_a")
def test_cross_a():
    """Test A"""
    print("✓ test_cross_a")
    assert True
