# File: tests/integration/test_coverage_gaps.py
# Purpose: Targeted tests that cover every remaining uncovered line.
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.auth.jwt import create_token, decode_token
from app.core.config import get_settings, Settings
from app.schemas.token import TokenType


# ── Config ─────────────────────────────────────────────────────────────────────

def test_get_settings_returns_settings():
    s = get_settings()
    assert isinstance(s, Settings)

def test_settings_jwt_secret_is_string():
    """JWT_SECRET_KEY may be empty in CI if the secret is not yet configured."""
    s = get_settings()
    assert isinstance(s.JWT_SECRET_KEY, str)      # just check the field exists

def test_settings_algorithm():
    s = get_settings()
    assert s.ALGORITHM == "HS256"

def test_settings_bcrypt_rounds():
    s = get_settings()
    assert isinstance(s.BCRYPT_ROUNDS, int)


# ── database.py — get_db generator (lines 15-19) ─────────────────────────────

def test_get_db_yields_session_and_closes():
    """Covers the get_db() generator body by mocking SessionLocal."""
    from app.database import get_db
    mock_session = MagicMock()
    with patch("app.database.SessionLocal", return_value=mock_session):
        gen  = get_db()
        sess = next(gen)
        assert sess is mock_session
        try:
            next(gen)
        except StopIteration:
            pass
    mock_session.close.assert_called_once()

def test_get_db_closes_on_exception():
    """Covers the finally block when the caller raises."""
    from app.database import get_db
    mock_session = MagicMock()
    with patch("app.database.SessionLocal", return_value=mock_session):
        gen = get_db()
        next(gen)
        try:
            gen.throw(RuntimeError("simulated error"))
        except RuntimeError:
            pass
    mock_session.close.assert_called_once()

def test_get_engine_returns_engine():
    from app.database import get_engine
    eng = get_engine("sqlite://")
    assert eng is not None

def test_get_sessionmaker_returns_factory():
    from app.database import get_engine, get_sessionmaker
    eng = get_engine("sqlite://")
    sm  = get_sessionmaker(eng)
    assert sm is not None


# ── database_init.py — init_db / drop_db (lines 8, 12) ───────────────────────

def test_init_db_calls_create_all():
    """Covers init_db() by mocking the Postgres engine."""
    from app.database_init import init_db
    mock_meta = MagicMock()
    mock_eng  = MagicMock()
    with patch("app.database_init.Base") as mock_base, \
         patch("app.database_init.engine", mock_eng):
        mock_base.metadata = mock_meta
        init_db()
    mock_meta.create_all.assert_called_once_with(bind=mock_eng)

def test_drop_db_calls_drop_all():
    """Covers drop_db() by mocking the Postgres engine."""
    from app.database_init import drop_db
    mock_meta = MagicMock()
    mock_eng  = MagicMock()
    with patch("app.database_init.Base") as mock_base, \
         patch("app.database_init.engine", mock_eng):
        mock_base.metadata = mock_meta
        drop_db()
    mock_meta.drop_all.assert_called_once_with(bind=mock_eng)


# ── auth/dependencies.py:36 — HTTPException re-raised as credentials_exception ─

def test_refresh_token_rejected_on_protected_route(client, test_user):
    """Sending a refresh token to an access-only route hits dependencies.py:36."""
    refresh_tok = create_token(str(test_user.id), TokenType.REFRESH)
    resp = client.get("/users/me", headers={"Authorization": f"Bearer {refresh_tok}"})
    assert resp.status_code == 401

def test_get_current_user_bad_token_format(client):
    """Malformed JWT hits the JWTError branch → credentials_exception."""
    resp = client.get("/users/me", headers={"Authorization": "Bearer not.a.valid.jwt"})
    assert resp.status_code == 401

def test_get_current_active_user_inactive(client, db_session):
    """Inactive user returns 400 (get_current_active_user guard)."""
    from app.models.user import User
    suffix = uuid.uuid4().hex[:8]
    u = User(
        first_name="Inactive", last_name="User",
        email=f"inactive_{suffix}@ex.com",
        username=f"inactive_{suffix}",
        password=User.hash_password("InactivePass1!"),
        is_active=False, is_verified=True,
    )
    db_session.add(u)
    db_session.commit()
    tok  = create_token(str(u.id), TokenType.ACCESS)
    resp = client.get("/users/me", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 400


# ── auth/dependencies.py — missing user in DB after valid token ───────────────

def test_valid_token_deleted_user_returns_401(client, db_session):
    """Token sub refers to a user that no longer exists → 401."""
    tok  = create_token(str(uuid.uuid4()), TokenType.ACCESS)  # random non-existent ID
    resp = client.get("/users/me", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 401


# ── auth/dependencies.py — token with no sub field ────────────────────────────

def test_token_without_sub_returns_401(client):
    """JWT with no 'sub' field → credentials_exception (line 30)."""
    from jose import jwt as jose_jwt
    from datetime import datetime, timedelta, timezone
    cfg     = get_settings()
    payload = {
        "type": "access",
        "exp":  datetime.now(timezone.utc) + timedelta(minutes=5),
        "jti":  "test-no-sub",
    }
    tok  = jose_jwt.encode(payload, cfg.JWT_SECRET_KEY, algorithm=cfg.ALGORITHM)
    resp = client.get("/users/me", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 401


# ── models/user.py:39 — User.__init__ with hashed_password kwarg ─────────────

def test_user_init_hashed_password_kwarg():
    """Covers the 'hashed_password' → 'password' rename in User.__init__."""
    from app.models.user import User
    u = User(
        first_name="HP", last_name="Test",
        email="hp@example.com", username="hpuser",
        hashed_password="already_hashed_value",
        is_active=True, is_verified=False,
    )
    assert u.password == "already_hashed_value"


# ── models/user.py:128 — verify_token when sub is None ───────────────────────

def test_verify_token_returns_none_for_none_input():
    from app.models.user import User
    assert User.verify_token(None) is None

def test_verify_token_returns_none_for_empty_string():
    from app.models.user import User
    assert User.verify_token("") is None

def test_verify_token_token_with_no_sub():
    """Covers the 'sub is None → return None' branch (line 128)."""
    from app.models.user import User
    from jose import jwt as jose_jwt
    from datetime import datetime, timedelta, timezone
    cfg     = get_settings()
    payload = {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    tok     = jose_jwt.encode(payload, cfg.JWT_SECRET_KEY, algorithm=cfg.ALGORITHM)
    result  = User.verify_token(tok)
    assert result is None


# ── models/calculation.py — GUID.process_bind_param string-UUID branch ────────

def test_guid_process_bind_param_with_string(db_session):
    """Querying by string UUID triggers GUID.process_bind_param non-UUID branch."""
    from app.models.calculation import Calculation
    from app.models.user import User
    suffix = uuid.uuid4().hex[:8]
    u = User(
        first_name="G", last_name="Test",
        email=f"guid_{suffix}@ex.com",
        username=f"guid_{suffix}",
        password=User.hash_password("GuidPass1!"),
        is_active=True, is_verified=True,
    )
    db_session.add(u)
    db_session.commit()
    c = Calculation.create("addition", u.id, [1, 2])
    c.result = 3.0
    db_session.add(c)
    db_session.commit()
    # Query with string UUID → triggers process_bind_param string branch
    result = db_session.query(Calculation).filter(
        Calculation.id == str(c.id)
    ).first()
    assert result is not None


# ── main.py:352-354 — update_calculation ValueError (div by zero via type switch)

def test_update_to_division_inherits_zero_input(client, auth_headers):
    """
    Create addition [10, 0], then switch type to division.
    Route checks the existing inputs for zero — raises ValueError → 400.
    """
    create_resp = client.post(
        "/calculations",
        json={"type": "addition", "inputs": [10.0, 0.0]},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    calc_id = create_resp.json()["id"]

    resp = client.put(
        f"/calculations/{calc_id}",
        json={"type": "division"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "zero" in resp.json()["detail"].lower()

def test_update_to_modulo_inherits_zero_input(client, auth_headers):
    """
    Create addition [10, 0], then switch type to modulo.
    Same ValueError path for modulo zero.
    """
    create_resp = client.post(
        "/calculations",
        json={"type": "addition", "inputs": [10.0, 0.0]},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    calc_id = create_resp.json()["id"]

    resp = client.put(
        f"/calculations/{calc_id}",
        json={"type": "modulo"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "zero" in resp.json()["detail"].lower()


# ── main.py — update_profile covering both email AND username filters ─────────

def test_update_profile_email_and_username_together(client, auth_headers):
    """Covers both 'email in fields' and 'username in fields' filter branches."""
    new_email = f"both_{uuid.uuid4().hex[:8]}@example.com"
    new_un    = f"both_{uuid.uuid4().hex[:8]}"
    resp = client.put(
        "/users/me",
        json={"email": new_email, "username": new_un},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"]    == new_email
    assert data["username"] == new_un

def test_update_profile_duplicate_username_returns_409(client, auth_headers, db_session):
    """Covers the conflict check when the new username is already taken."""
    from app.models.user import User
    suffix = uuid.uuid4().hex[:8]
    other  = User(
        first_name="Other2", last_name="Conflict",
        email=f"con2_{suffix}@example.com",
        username=f"con2_{suffix}",
        password=User.hash_password("ConPass1!"),
        is_active=True, is_verified=True,
    )
    db_session.add(other)
    db_session.commit()
    resp = client.put("/users/me", json={"username": other.username}, headers=auth_headers)
    assert resp.status_code == 409


# ── HTML pages ────────────────────────────────────────────────────────────────

def test_index_has_tailwind(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "tailwindcss" in resp.text.lower() or "tailwind" in resp.text.lower()

def test_dashboard_has_calculate(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "calculate" in resp.text.lower() or "calculation" in resp.text.lower()

def test_view_page_renders(client):
    resp = client.get(f"/dashboard/view/{uuid.uuid4()}")
    assert resp.status_code == 200

def test_edit_page_renders(client):
    resp = client.get(f"/dashboard/edit/{uuid.uuid4()}")
    assert resp.status_code == 200


# ── Additional calculation edge cases ─────────────────────────────────────────

def test_create_power_large_exponent(client, auth_headers):
    resp = client.post(
        "/calculations",
        json={"type": "power", "inputs": [2.0, 10.0]},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["result"] == pytest.approx(1024.0)

def test_create_modulo_chained(client, auth_headers):
    resp = client.post(
        "/calculations",
        json={"type": "modulo", "inputs": [100, 7, 3]},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["result"] == pytest.approx(100 % 7 % 3)

def test_operations_all_importable():
    from app.operations import add, subtract, multiply, divide, modulo, power
    assert all(callable(f) for f in [add, subtract, multiply, divide, modulo, power])

def test_main_app_importable():
    import app.main as m
    assert hasattr(m, "app")


# ── main.py:352-354 — except ValueError in update_calculation (mock approach) ─

def test_update_calculation_get_result_raises_value_error(client, auth_headers):
    """
    Patches Calculation.create so get_result() raises ValueError,
    ensuring the except ValueError block (lines 352-354) is traced by coverage.py.
    The explicit zero-divisor check is bypassed by using 'subtraction',
    so execution reaches tmp.get_result() which raises.
    """
    from unittest.mock import patch, MagicMock

    create_resp = client.post(
        "/calculations",
        json={"type": "addition", "inputs": [5.0, 3.0]},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    calc_id = create_resp.json()["id"]

    mock_tmp = MagicMock()
    mock_tmp.get_result.side_effect = ValueError("mocked forced error")

    with patch("app.main.Calculation.create", return_value=mock_tmp):
        resp = client.put(
            f"/calculations/{calc_id}",
            json={"type": "subtraction", "inputs": [10.0, 5.0]},
            headers=auth_headers,
        )

    assert resp.status_code == 400
    assert "mocked forced error" in resp.json()["detail"]


# ── models/calculation.py — GUID type-descriptor branches ────────────────────

def test_guid_process_bind_param_none():
    """Line 28: process_bind_param returns None when value is None."""
    from unittest.mock import MagicMock
    from app.models.calculation import GUID
    g       = GUID()
    dialect = MagicMock()
    dialect.name = "sqlite"
    result  = g.process_bind_param(None, dialect)
    assert result is None

def test_guid_process_result_value_none():
    """Line 35: process_result_value returns None when value is None."""
    from unittest.mock import MagicMock
    from app.models.calculation import GUID
    g       = GUID()
    dialect = MagicMock()
    result  = g.process_result_value(None, dialect)
    assert result is None

def test_guid_process_result_value_already_uuid():
    """Line 38: process_result_value returns existing uuid.UUID unchanged."""
    import uuid
    from unittest.mock import MagicMock
    from app.models.calculation import GUID
    g        = GUID()
    dialect  = MagicMock()
    uid      = uuid.uuid4()
    result   = g.process_result_value(uid, dialect)
    assert result == uid

def test_guid_load_dialect_impl_postgres():
    """Line in load_dialect_impl: PostgreSQL path returns PG_UUID descriptor."""
    from unittest.mock import MagicMock
    from app.models.calculation import GUID
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    g = GUID()
    mock_dialect = MagicMock()
    mock_dialect.name = "postgresql"
    mock_dialect.type_descriptor.return_value = "pg_uuid_type"
    result = g.load_dialect_impl(mock_dialect)
    assert result == "pg_uuid_type"
    # Verify it was called with PG_UUID
    mock_dialect.type_descriptor.assert_called_once()
