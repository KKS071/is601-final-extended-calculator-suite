# File: tests/integration/test_calculation_model.py
# Purpose: Integration tests for Calculation model with a real DB session.
import uuid
import pytest

from app.models.calculation import Calculation
from app.models.user import User


def _user(db):
    suffix = uuid.uuid4().hex[:8]
    u = User.register(db, {
        "first_name": "Calc", "last_name": "Test",
        "email":      f"calc_{suffix}@ex.com",
        "username":   f"calc_{suffix}",
        "password":   "CalcPass123!",
    })
    db.commit()
    db.refresh(u)
    return u


def test_add_and_retrieve_addition(db_session):
    user = _user(db_session)
    calc = Calculation.create("addition", user.id, [5, 3, 2])
    calc.result = calc.get_result()
    db_session.add(calc)
    db_session.commit()
    db_session.refresh(calc)
    assert calc.result == 10.0
    assert calc.type   == "addition"
    assert calc.user_id == user.id

def test_add_and_retrieve_modulo(db_session):
    user = _user(db_session)
    calc = Calculation.create("modulo", user.id, [10, 3])
    calc.result = calc.get_result()
    db_session.add(calc)
    db_session.commit()
    db_session.refresh(calc)
    assert calc.result == pytest.approx(1.0)

def test_add_and_retrieve_power(db_session):
    user = _user(db_session)
    calc = Calculation.create("power", user.id, [2, 10])
    calc.result = calc.get_result()
    db_session.add(calc)
    db_session.commit()
    db_session.refresh(calc)
    assert calc.result == pytest.approx(1024.0)

def test_cascade_delete(db_session):
    user = _user(db_session)
    calc = Calculation.create("addition", user.id, [1, 2])
    calc.result = 3.0
    db_session.add(calc)
    db_session.commit()
    calc_id = calc.id

    db_session.delete(user)
    db_session.commit()

    gone = db_session.query(Calculation).filter_by(id=calc_id).first()
    assert gone is None

def test_all_six_types_persist(db_session):
    user   = _user(db_session)
    types  = [
        ("addition",       [1, 2]),
        ("subtraction",    [10, 3]),
        ("multiplication", [4, 5]),
        ("division",       [20, 4]),
        ("modulo",         [11, 4]),
        ("power",          [3, 2]),
    ]
    for ctype, inputs in types:
        c = Calculation.create(ctype, user.id, inputs)
        c.result = c.get_result()
        db_session.add(c)
    db_session.commit()

    results = db_session.query(Calculation).filter_by(user_id=user.id).all()
    assert len(results) == 6

def test_created_at_set(db_session):
    user = _user(db_session)
    calc = Calculation.create("addition", user.id, [1, 2])
    calc.result = 3.0
    db_session.add(calc)
    db_session.commit()
    db_session.refresh(calc)
    assert calc.created_at is not None
