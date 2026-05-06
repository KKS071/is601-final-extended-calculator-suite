# File: tests/unit/test_calculation_model.py
# Purpose: Unit tests for Calculation model logic — all six types, factory, edge cases.
import uuid
import pytest

from app.models.calculation import (
    Addition, Subtraction, Multiplication, Division, Modulo, Power, Calculation,
)


def uid(): return uuid.uuid4()


# ── Addition ──────────────────────────────────────────────────────────────────
def test_addition_two_values():     assert Addition(user_id=uid(), inputs=[3, 4]).get_result() == 7.0
def test_addition_three_values():   assert Addition(user_id=uid(), inputs=[1, 2, 3]).get_result() == 6.0
def test_addition_five_values():    assert Addition(user_id=uid(), inputs=[1,1,1,1,1]).get_result() == 5.0
def test_addition_floats():         assert Addition(user_id=uid(), inputs=[1.5, 2.5, 3.0]).get_result() == 7.0
def test_addition_non_list_raises():
    with pytest.raises(ValueError, match="must be a list"):
        Addition(user_id=uid(), inputs="bad").get_result()
def test_addition_one_input_raises():
    with pytest.raises(ValueError, match="two"):
        Addition(user_id=uid(), inputs=[5]).get_result()


# ── Subtraction ───────────────────────────────────────────────────────────────
def test_subtraction_two_values():   assert Subtraction(user_id=uid(), inputs=[20, 5]).get_result() == 15.0
def test_subtraction_three_values(): assert Subtraction(user_id=uid(), inputs=[100, 30, 20]).get_result() == 50.0
def test_subtraction_non_list_raises():
    with pytest.raises(ValueError):
        Subtraction(user_id=uid(), inputs=None).get_result()


# ── Multiplication ────────────────────────────────────────────────────────────
def test_multiplication_two():    assert Multiplication(user_id=uid(), inputs=[3, 4]).get_result() == 12.0
def test_multiplication_three():  assert Multiplication(user_id=uid(), inputs=[2, 3, 4]).get_result() == 24.0
def test_multiplication_five():   assert Multiplication(user_id=uid(), inputs=[1,2,3,4,5]).get_result() == 120.0
def test_multiplication_zero():   assert Multiplication(user_id=uid(), inputs=[5, 0, 10]).get_result() == 0.0


# ── Division ──────────────────────────────────────────────────────────────────
def test_division_two():    assert Division(user_id=uid(), inputs=[20, 4]).get_result() == 5.0
def test_division_three():  assert Division(user_id=uid(), inputs=[100, 5, 4]).get_result() == 5.0
def test_division_by_zero_raises():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        Division(user_id=uid(), inputs=[10, 0]).get_result()
def test_division_non_list_raises():
    with pytest.raises(ValueError):
        Division(user_id=uid(), inputs="x").get_result()


# ── Modulo ────────────────────────────────────────────────────────────────────
def test_modulo_basic():     assert Modulo(user_id=uid(), inputs=[10, 3]).get_result() == 1.0
def test_modulo_exact():     assert Modulo(user_id=uid(), inputs=[9, 3]).get_result() == 0.0
def test_modulo_chained():   assert Modulo(user_id=uid(), inputs=[100, 7, 3]).get_result() == pytest.approx(100 % 7 % 3)
def test_modulo_non_list_raises():
    with pytest.raises(ValueError, match="must be a list"):
        Modulo(user_id=uid(), inputs="bad").get_result()
def test_modulo_one_input_raises():
    with pytest.raises(ValueError, match="two"):
        Modulo(user_id=uid(), inputs=[5]).get_result()
def test_modulo_by_zero_raises():
    with pytest.raises(ValueError, match="Cannot modulo by zero"):
        Modulo(user_id=uid(), inputs=[10, 0]).get_result()


# ── Power ─────────────────────────────────────────────────────────────────────
def test_power_basic():     assert Power(user_id=uid(), inputs=[2, 3]).get_result() == 8.0
def test_power_zero_exp():  assert Power(user_id=uid(), inputs=[5, 0]).get_result() == 1.0
def test_power_float():     assert Power(user_id=uid(), inputs=[4, 0.5]).get_result() == pytest.approx(2.0)
def test_power_chained():   assert Power(user_id=uid(), inputs=[2, 3, 2]).get_result() == pytest.approx(64.0)
def test_power_non_list_raises():
    with pytest.raises(ValueError, match="must be a list"):
        Power(user_id=uid(), inputs="bad").get_result()
def test_power_one_input_raises():
    with pytest.raises(ValueError, match="two"):
        Power(user_id=uid(), inputs=[5]).get_result()


# ── Factory ───────────────────────────────────────────────────────────────────
def test_factory_addition():       assert isinstance(Calculation.create("addition",       uid(), [1, 2]), Addition)
def test_factory_subtraction():    assert isinstance(Calculation.create("subtraction",    uid(), [1, 2]), Subtraction)
def test_factory_multiplication(): assert isinstance(Calculation.create("multiplication", uid(), [1, 2]), Multiplication)
def test_factory_division():       assert isinstance(Calculation.create("division",       uid(), [10, 2]), Division)
def test_factory_modulo():         assert isinstance(Calculation.create("modulo",         uid(), [10, 3]), Modulo)
def test_factory_power():          assert isinstance(Calculation.create("power",          uid(), [2, 3]), Power)
def test_factory_case_insensitive(): assert isinstance(Calculation.create("ADDITION", uid(), [1, 2]), Addition)
def test_factory_invalid_raises():
    with pytest.raises(ValueError, match="Unsupported"):
        Calculation.create("square_root", uid(), [4])
def test_factory_multi_value_result():
    c = Calculation.create("multiplication", uid(), [2, 3, 4])
    assert c.get_result() == 24.0
def test_base_get_result_raises():
    calc = Calculation(user_id=uid(), inputs=[1, 2])
    with pytest.raises(NotImplementedError):
        calc.get_result()
def test_repr_contains_type():
    c = Addition(user_id=uid(), inputs=[1, 2])
    assert "addition" in repr(c).lower() or "Calculation" in repr(c)
