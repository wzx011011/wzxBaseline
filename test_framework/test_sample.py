import pytest

def test_example():
    """A simple test to verify the testing framework is working."""
    assert True

def test_math():
    """A simple math test."""
    assert 1 + 1 == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])