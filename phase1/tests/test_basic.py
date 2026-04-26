"""
Basic test cases to verify test infrastructure is working
"""

import pytest


def test_basic_math():
    """Test basic math operations"""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
    assert 10 / 2 == 5


def test_string_operations():
    """Test basic string operations"""
    assert "hello" + " " + "world" == "hello world"
    assert "test".upper() == "TEST"
    assert "PYTHON".lower() == "python"
    assert len("testing") == 7


def test_list_operations():
    """Test basic list operations"""
    numbers = [1, 2, 3, 4, 5]
    assert len(numbers) == 5
    assert numbers[0] == 1
    assert numbers[-1] == 5
    assert 3 in numbers
    assert 6 not in numbers


def test_dictionary_operations():
    """Test basic dictionary operations"""
    data = {"name": "Test", "value": 123}
    assert data["name"] == "Test"
    assert data["value"] == 123
    assert "name" in data
    assert "missing" not in data
    assert len(data) == 2


class TestBasicClass:
    """Test basic class functionality"""
    
    def test_class_instantiation(self):
        """Test creating a simple class"""
        class SimpleClass:
            def __init__(self, value):
                self.value = value
            
            def get_value(self):
                return self.value
        
        obj = SimpleClass(42)
        assert obj.value == 42
        assert obj.get_value() == 42
    
    def test_class_methods(self):
        """Test class methods"""
        class Calculator:
            def add(self, a, b):
                return a + b
            
            def multiply(self, a, b):
                return a * b
        
        calc = Calculator()
        assert calc.add(2, 3) == 5
        assert calc.multiply(4, 5) == 20


def test_exception_handling():
    """Test exception handling"""
    with pytest.raises(ValueError):
        raise ValueError("Test error")
    
    with pytest.raises(ZeroDivisionError):
        result = 1 / 0


def test_truthy_falsy():
    """Test truthy and falsy values"""
    assert True is True
    assert False is False
    assert not None
    assert not ""
    assert not []
    assert not {}
    assert "hello"
    assert [1, 2, 3]
    assert {"key": "value"}


@pytest.mark.parametrize("input_val,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (4, 8),
    (5, 10),
])
def test_parameterized(input_val, expected):
    """Test with parameterized inputs"""
    assert input_val * 2 == expected
