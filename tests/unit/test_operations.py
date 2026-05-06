# File: tests/unit/test_operations.py
# Purpose: Unit tests for pure arithmetic functions in app/operations.py.
import pytest
from app.operations import add, subtract, multiply, divide, modulo, power


def test_add_integers():       assert add(2, 3) == 5
def test_add_floats():         assert add(2.5, 1.5) == 4.0
def test_add_negative():       assert add(-1, 1) == 0

def test_subtract_positive():       assert subtract(10, 4) == 6
def test_subtract_negative_result(): assert subtract(3, 5) == -2

def test_multiply_integers():  assert multiply(3, 4) == 12
def test_multiply_by_zero():   assert multiply(5, 0) == 0

def test_divide_evenly():      assert divide(10, 2) == 5.0
def test_divide_float_result(): assert divide(7, 2) == 3.5
def test_divide_by_zero_raises():
    with pytest.raises(ValueError, match="Cannot divide by zero!"):
        divide(5, 0)

def test_modulo_basic():       assert modulo(10, 3) == 1
def test_modulo_exact():       assert modulo(9, 3) == 0
def test_modulo_by_zero_raises():
    with pytest.raises(ValueError, match="Cannot modulo by zero!"):
        modulo(5, 0)

def test_power_basic():        assert power(2, 3) == 8.0
def test_power_zero_exp():     assert power(5, 0) == 1.0
def test_power_float():        assert power(4, 0.5) == 2.0
