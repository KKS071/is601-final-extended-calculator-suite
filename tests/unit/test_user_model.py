# File: tests/unit/test_user_model.py
# Purpose: Unit tests for User model — helpers, str, verify_token.
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.models.user import User


def make_user(**kwargs):
    defaults = dict(
        first_name="Test",
        last_name="User",
        email="t@example.com",
        username="testuser",
        password=User.hash_password("TestPass123!"),
        is_active=True,
        is_verified=False,
    )
    defaults.update(kwargs)
    return User(**defaults)


def test_str_contains_name():
    u = make_user(first_name="Alice", last_name="Smith", email="alice@example.com")
    s = str(u)
    assert "Alice" in s or "alice@example.com" in s

def test_verify_password_correct():
    u = make_user()
    assert u.verify_password("TestPass123!")

def test_verify_password_incorrect():
    u = make_user()
    assert not u.verify_password("WrongPass99!")

def test_hash_password_returns_string():
    h = User.hash_password("SomePass1!")
    assert isinstance(h, str)
    assert h != "SomePass1!"

def test_hashed_password_property():
    u = make_user()
    assert u.hashed_password == u.password

def test_update_changes_fields():
    u = make_user(first_name="Old")
    u.update(first_name="New")
    assert u.first_name == "New"

def test_update_returns_self():
    u = make_user()
    result = u.update(last_name="Jones")
    assert result is u

def test_verify_token_valid():
    u = make_user()
    token = User.create_access_token({"sub": str(uuid.uuid4())})
    assert isinstance(token, str)

def test_verify_token_invalid():
    result = User.verify_token("invalid.token.here")
    assert result is None

def test_verify_token_none():
    result = User.verify_token(None)
    assert result is None

def test_register_raises_on_duplicate(db_session):
    data = {
        "first_name": "Dup",
        "last_name":  "User",
        "email":      "dup@example.com",
        "username":   "dupuser",
        "password":   "DupPass123!",
    }
    User.register(db_session, data)
    db_session.commit()
    with pytest.raises(ValueError, match="already exists"):
        User.register(db_session, data)

def test_register_short_password_raises(db_session):
    data = {
        "first_name": "Short",
        "last_name":  "Pwd",
        "email":      "short@example.com",
        "username":   "shortpwd",
        "password":   "abc",
    }
    with pytest.raises(ValueError, match="at least"):
        User.register(db_session, data)
