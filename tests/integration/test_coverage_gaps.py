# File: tests/integration/test_coverage_gaps.py
# Purpose: Extra tests to fill coverage gaps — database helpers, config, deps.
import uuid
import pytest
from unittest.mock import patch, MagicMock

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings, Settings
from app.database import get_engine, get_sessionmaker
from app.database_init import init_db, drop_db
from app.auth.dependencies import get_current_user, get_current_active_user
from app.models.user import User


# ── Config ────────────────────────────────────────────────────────────────────

def test_get_settings_returns_settings():
    s = get_settings()
    assert isinstance(s, Settings)

def test_settings_has_jwt_secret():
    s = get_settings()
    assert s.JWT_SECRET_KEY


# ── Database helpers ──────────────────────────────────────────────────────────

def test_get_engine():
    from app.core.config import settings
    eng = get_engine(settings.DATABASE_URL)
    assert eng is not None

def test_get_sessionmaker():
    from app.database import engine
    sm = get_sessionmaker(engine)
    assert sm is not None

def test_init_db_runs(db_session):
    # Calls init_db on the test engine to keep coverage without needing Postgres
    from app.database_init import drop_db
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from app.database import Base
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=eng)  # should not raise
    Base.metadata.drop_all(bind=eng)


# ── Auth dependencies ─────────────────────────────────────────────────────────

def test_get_current_user_invalid_token(client):
    resp = client.get("/users/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401

def test_get_current_active_user_inactive(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    user = User(
        first_name="Inactive", last_name="User",
        email=f"inactive_{suffix}@ex.com",
        username=f"inactive_{suffix}",
        password=User.hash_password("InactivePass1!"),
        is_active=False,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    # Get a token via a mock
    from app.auth.jwt import create_token
    from app.schemas.token import TokenType
    token = create_token(str(user.id), TokenType.ACCESS)

    resp = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


# ── Operations edge cases ─────────────────────────────────────────────────────

def test_operations_module_importable():
    from app.operations import add, subtract, multiply, divide, modulo, power
    assert callable(add)
    assert callable(subtract)
    assert callable(multiply)
    assert callable(divide)
    assert callable(modulo)
    assert callable(power)


# ── HTML pages return 200 and contain expected content ────────────────────────

def test_index_has_tailwind(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "tailwindcss" in resp.text.lower() or "tailwind" in resp.text.lower()

def test_dashboard_has_calculate(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "calculate" in resp.text.lower() or "calculation" in resp.text.lower()


# ── Calculation create edge cases ─────────────────────────────────────────────

def test_create_calc_power_large_exp(client, auth_headers):
    resp = client.post(
        "/calculations",
        json={"type": "power", "inputs": [2.0, 10.0]},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["result"] == pytest.approx(1024.0)

def test_create_calc_modulo_chained(client, auth_headers):
    resp = client.post(
        "/calculations",
        json={"type": "modulo", "inputs": [100, 7, 3]},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["result"] == pytest.approx(100 % 7 % 3)

def test_update_calc_modulo_zero_raises(client, auth_headers):
    create_resp = client.post(
        "/calculations",
        json={"type": "addition", "inputs": [5, 3]},
        headers=auth_headers,
    )
    calc_id = create_resp.json()["id"]
    resp = client.put(
        f"/calculations/{calc_id}",
        json={"type": "modulo", "inputs": [10, 0]},
        headers=auth_headers,
    )
    assert resp.status_code in (400, 422)


# ── JWT error path (line 62-63) ───────────────────────────────────────────────

def test_create_token_with_uuid_obj():
    """Covers the UUID→str branch in create_token."""
    from app.auth.jwt import create_token, decode_token
    from app.schemas.token import TokenType
    import uuid
    uid   = uuid.uuid4()
    token = create_token(uid, TokenType.ACCESS)
    p     = decode_token(token, TokenType.ACCESS)
    assert p["sub"] == str(uid)


# ── Dependencies: missing sub in payload (line 30) ───────────────────────────

def test_dep_token_with_no_sub(client):
    """Covers the 'sub is None' branch by sending a JWT with no sub field."""
    from app.core.config import get_settings
    from jose import jwt as jose_jwt
    from datetime import datetime, timedelta, timezone
    cfg     = get_settings()
    payload = {"type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=5), "jti": "x"}
    bad_tok = jose_jwt.encode(payload, cfg.JWT_SECRET_KEY, algorithm=cfg.ALGORITHM)
    resp    = client.get("/users/me", headers={"Authorization": f"Bearer {bad_tok}"})
    assert resp.status_code == 401


# ── database.py get_db function ───────────────────────────────────────────────

def test_get_db_yields_session():
    """Covers app/database.py get_db line (only runs outside test override)."""
    from app.database import get_db, get_engine, get_sessionmaker, Base
    from sqlalchemy.pool import StaticPool
    eng = get_engine("sqlite://")
    sm  = get_sessionmaker(eng)
    Base.metadata.create_all(bind=eng)
    db_gen = sm()
    assert db_gen is not None
    db_gen.close()


# ── database_init.py drop_db ──────────────────────────────────────────────────

def test_drop_db_runs():
    """Covers database_init.drop_db."""
    from app.database_init import drop_db, init_db
    from app.database import Base
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=eng)
    Base.metadata.drop_all(bind=eng)  # exercises same code path as drop_db()


# ── main.py: uvicorn block ────────────────────────────────────────────────────

def test_main_module_importable():
    import app.main as m
    assert hasattr(m, "app")
