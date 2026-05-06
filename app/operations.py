# File: app/operations.py
# Purpose: Pure arithmetic functions used by the Calculation model.
from typing import Union

Number = Union[int, float]


def add(a: Number, b: Number) -> Number:
    return a + b


def subtract(a: Number, b: Number) -> Number:
    return a - b


def multiply(a: Number, b: Number) -> Number:
    return a * b


def divide(a: Number, b: Number) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    return a / b


def modulo(a: Number, b: Number) -> Number:
    """Return a mod b. Raises ValueError if b is zero."""
    if b == 0:
        raise ValueError("Cannot modulo by zero!")
    return a % b


def power(a: Number, b: Number) -> float:
    """Return a raised to the power of b."""
    return float(a ** b)
