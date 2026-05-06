# File: tests/unit/test_schemas.py
# Purpose: Unit tests for Pydantic schemas — validation rules, edge cases.
import pytest
from pydantic import ValidationError

from app.schemas.calculation import CalculationBase, CalculationCreate, CalculationUpdate, CalculationType
from app.schemas.user import UserCreate, UserUpdate, PasswordUpdate


# ── CalculationBase ───────────────────────────────────────────────────────────

def test_calculation_base_valid_addition():
    c = CalculationBase(type="addition", inputs=[1, 2])
    assert c.type == CalculationType.ADDITION
    assert c.inputs == [1.0, 2.0]

def test_calculation_base_valid_modulo():
    c = CalculationBase(type="modulo", inputs=[10, 3])
    assert c.type == CalculationType.MODULO

def test_calculation_base_valid_power():
    c = CalculationBase(type="power", inputs=[2, 8])
    assert c.type == CalculationType.POWER

def test_calculation_base_coerces_string_inputs():
    c = CalculationBase(type="addition", inputs="5, 10, 3")
    assert c.inputs == [5.0, 10.0, 3.0]

def test_calculation_base_normalizes_type_uppercase():
    c = CalculationBase(type="MULTIPLICATION", inputs=[2, 3])
    assert c.type == CalculationType.MULTIPLICATION

def test_calculation_base_too_few_inputs_raises():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", inputs=[1])

def test_calculation_base_invalid_type_raises():
    with pytest.raises(ValidationError):
        CalculationBase(type="logarithm", inputs=[1, 2])

def test_calculation_base_division_by_zero_raises():
    with pytest.raises(ValidationError):
        CalculationBase(type="division", inputs=[10, 0])

def test_calculation_base_modulo_by_zero_raises():
    with pytest.raises(ValidationError):
        CalculationBase(type="modulo", inputs=[10, 0])

def test_calculation_base_non_numeric_string_raises():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", inputs="abc, def")

def test_calculation_base_empty_inputs_raises():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", inputs=[])

def test_calculation_base_non_list_non_string_raises():
    with pytest.raises(ValidationError):
        CalculationBase(type="addition", inputs=42)

def test_calculation_base_all_types():
    for t in ["addition", "subtraction", "multiplication", "division", "modulo", "power"]:
        inputs = [10.0, 2.0]
        if t == "power":
            inputs = [2.0, 3.0]
        c = CalculationBase(type=t, inputs=inputs)
        assert c.type.value == t


# ── CalculationUpdate ─────────────────────────────────────────────────────────

def test_calc_update_partial():
    u = CalculationUpdate(inputs=[3, 4])
    assert u.inputs == [3.0, 4.0]
    assert u.type is None

def test_calc_update_type_only():
    u = CalculationUpdate(type="subtraction")
    assert u.type == CalculationType.SUBTRACTION
    assert u.inputs is None

def test_calc_update_empty():
    u = CalculationUpdate()
    assert u.type is None
    assert u.inputs is None

def test_calc_update_too_few_inputs_raises():
    with pytest.raises(ValidationError):
        CalculationUpdate(inputs=[1])

def test_calc_update_normalizes_type():
    u = CalculationUpdate(type="POWER")
    assert u.type == CalculationType.POWER

def test_calc_update_string_inputs():
    u = CalculationUpdate(inputs="1,2,3")
    assert u.inputs == [1.0, 2.0, 3.0]

def test_calc_update_bad_string_inputs_raises():
    with pytest.raises(ValidationError):
        CalculationUpdate(inputs="a,b,c")

def test_calc_update_none_inputs_allowed():
    u = CalculationUpdate(inputs=None)
    assert u.inputs is None

def test_calc_update_none_type_allowed():
    u = CalculationUpdate(type=None)
    assert u.type is None

def test_calc_update_invalid_type_raises():
    with pytest.raises(ValidationError):
        CalculationUpdate(type="foobar")

def test_calc_update_non_list_raises():
    with pytest.raises(ValidationError):
        CalculationUpdate(inputs=99)


# ── UserCreate ────────────────────────────────────────────────────────────────

def test_user_create_valid():
    u = UserCreate(
        first_name="Alice", last_name="Smith",
        email="alice@example.com", username="alice01",
        password="SecurePass123!", confirm_password="SecurePass123!"
    )
    assert u.username == "alice01"

def test_user_create_password_mismatch_raises():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="Alice", last_name="Smith",
            email="alice@example.com", username="alice01",
            password="SecurePass123!", confirm_password="DifferentPass1!"
        )

def test_user_create_no_uppercase_raises():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="A", last_name="B", email="a@b.com", username="ab123",
            password="lowercase1!", confirm_password="lowercase1!"
        )

def test_user_create_no_lowercase_raises():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="A", last_name="B", email="a@b.com", username="ab123",
            password="UPPERCASE1!", confirm_password="UPPERCASE1!"
        )

def test_user_create_no_digit_raises():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="A", last_name="B", email="a@b.com", username="ab123",
            password="NoDigitPass!", confirm_password="NoDigitPass!"
        )

def test_user_create_no_special_char_raises():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="A", last_name="B", email="a@b.com", username="ab123",
            password="NoSpecial123", confirm_password="NoSpecial123"
        )

def test_user_create_invalid_email_raises():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="A", last_name="B", email="not_an_email", username="ab123",
            password="ValidPass1!", confirm_password="ValidPass1!"
        )

def test_user_create_short_username_raises():
    with pytest.raises(ValidationError):
        UserCreate(
            first_name="A", last_name="B", email="a@b.com", username="ab",
            password="ValidPass1!", confirm_password="ValidPass1!"
        )


# ── PasswordUpdate ────────────────────────────────────────────────────────────

def test_password_update_valid():
    p = PasswordUpdate(
        current_password="OldPass123!",
        new_password="NewPass456!",
        confirm_new_password="NewPass456!"
    )
    assert p.new_password == "NewPass456!"

def test_password_update_mismatch_raises():
    with pytest.raises(ValidationError):
        PasswordUpdate(
            current_password="OldPass123!",
            new_password="NewPass456!",
            confirm_new_password="Different1!"
        )

def test_password_update_same_as_current_raises():
    with pytest.raises(ValidationError):
        PasswordUpdate(
            current_password="SamePass1!",
            new_password="SamePass1!",
            confirm_new_password="SamePass1!"
        )


# ── UserUpdate ────────────────────────────────────────────────────────────────

def test_user_update_partial():
    u = UserUpdate(email="new@example.com")
    assert u.email == "new@example.com"
    assert u.first_name is None

def test_user_update_all_none():
    u = UserUpdate()
    assert all(v is None for v in [u.first_name, u.last_name, u.email, u.username])

def test_user_update_invalid_email_raises():
    with pytest.raises(ValidationError):
        UserUpdate(email="not_valid")
