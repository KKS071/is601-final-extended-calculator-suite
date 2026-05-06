# File: tests/integration/test_user_model.py
# Purpose: Integration tests for User model using a real DB session.
import uuid
import pytest

from app.models.user import User


def _make_user(db, **overrides):
    suffix = uuid.uuid4().hex[:8]
    data = {
        "first_name": "Int",
        "last_name":  "Test",
        "email":      f"int_{suffix}@example.com",
        "username":   f"int_{suffix}",
        "password":   "IntPass123!",
    }
    data.update(overrides)
    user = User.register(db, data)
    db.commit()
    db.refresh(user)
    return user


def test_register_creates_user(db_session):
    user = _make_user(db_session)
    assert user.id is not None
    assert user.is_active is True

def test_password_is_hashed(db_session):
    user = _make_user(db_session)
    assert user.password != "IntPass123!"

def test_authenticate_success(db_session):
    user = _make_user(db_session)
    result = User.authenticate(db_session, user.username, "IntPass123!")
    assert result is not None
    assert "access_token" in result

def test_authenticate_by_email(db_session):
    user = _make_user(db_session)
    result = User.authenticate(db_session, user.email, "IntPass123!")
    assert result is not None

def test_authenticate_wrong_password(db_session):
    user = _make_user(db_session)
    result = User.authenticate(db_session, user.username, "WrongPass99!")
    assert result is None

def test_authenticate_unknown_user(db_session):
    result = User.authenticate(db_session, "ghost_user", "Pass123!")
    assert result is None

def test_update_persists(db_session):
    user = _make_user(db_session)
    user.update(first_name="UpdatedName")
    db_session.commit()
    db_session.refresh(user)
    assert user.first_name == "UpdatedName"

def test_verify_token_round_trip(db_session):
    user  = _make_user(db_session)
    token = User.create_access_token({"sub": str(user.id)})
    result = User.verify_token(token)
    assert result == user.id

def test_user_str(db_session):
    user = _make_user(db_session)
    s = str(user)
    assert "Int" in s or user.email in s

def test_duplicate_email_raises(db_session):
    user = _make_user(db_session)
    with pytest.raises(ValueError, match="already exists"):
        _make_user(db_session, email=user.email, username=f"new_{uuid.uuid4().hex[:8]}")

def test_duplicate_username_raises(db_session):
    user = _make_user(db_session)
    with pytest.raises(ValueError, match="already exists"):
        _make_user(db_session, username=user.username, email=f"new_{uuid.uuid4().hex[:8]}@x.com")

def test_authenticate_sets_last_login(db_session):
    user = _make_user(db_session)
    User.authenticate(db_session, user.username, "IntPass123!")
    db_session.refresh(user)
    assert user.last_login is not None
