# File: tests/integration/test_api_auth.py
# Purpose: Integration tests for /auth/register and /auth/login.
import uuid
import pytest


def unique_payload(**overrides):
    suffix = uuid.uuid4().hex[:8]
    base = {
        "first_name": "Alice",
        "last_name":  "Auth",
        "email":      f"alice_{suffix}@example.com",
        "username":   f"alice_{suffix}",
        "password":   "SecurePass1!",
        "confirm_password": "SecurePass1!",
    }
    base.update(overrides)
    return base


# ── Register ──────────────────────────────────────────────────────────────────

def test_register_success(client):
    resp = client.post("/auth/register", json=unique_payload())
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert "password" not in data

def test_register_duplicate_email(client):
    payload = unique_payload()
    client.post("/auth/register", json=payload)
    dup = unique_payload(email=payload["email"], username=f"other_{uuid.uuid4().hex[:6]}")
    resp = client.post("/auth/register", json=dup)
    assert resp.status_code == 400

def test_register_duplicate_username(client):
    payload = unique_payload()
    client.post("/auth/register", json=payload)
    dup = unique_payload(username=payload["username"], email=f"other_{uuid.uuid4().hex[:6]}@x.com")
    resp = client.post("/auth/register", json=dup)
    assert resp.status_code == 400

def test_register_password_mismatch(client):
    payload = unique_payload(confirm_password="DifferentPass1!")
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 422

def test_register_weak_password_no_uppercase(client):
    resp = client.post("/auth/register", json=unique_payload(password="nouppercase1!", confirm_password="nouppercase1!"))
    assert resp.status_code == 422

def test_register_weak_password_no_digit(client):
    resp = client.post("/auth/register", json=unique_payload(password="NoDigitPass!", confirm_password="NoDigitPass!"))
    assert resp.status_code == 422

def test_register_weak_password_no_special(client):
    resp = client.post("/auth/register", json=unique_payload(password="NoSpecial123", confirm_password="NoSpecial123"))
    assert resp.status_code == 422

def test_register_invalid_email(client):
    resp = client.post("/auth/register", json=unique_payload(email="not-an-email"))
    assert resp.status_code == 422

def test_register_missing_fields(client):
    resp = client.post("/auth/register", json={"username": "only"})
    assert resp.status_code == 422

def test_register_short_username(client):
    resp = client.post("/auth/register", json=unique_payload(username="ab"))
    assert resp.status_code == 422


# ── Login JSON ────────────────────────────────────────────────────────────────

def test_login_success(client):
    payload = unique_payload()
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/login", json={
        "username": payload["username"],
        "password": payload["password"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user_id" in data

def test_login_wrong_password(client):
    payload = unique_payload()
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/login", json={"username": payload["username"], "password": "WrongPass1!"})
    assert resp.status_code == 401

def test_login_unknown_user(client):
    resp = client.post("/auth/login", json={"username": "ghost_user", "password": "SomePass1!"})
    assert resp.status_code == 401

def test_login_missing_fields(client):
    resp = client.post("/auth/login", json={"username": "only"})
    assert resp.status_code == 422

def test_login_by_email(client):
    payload = unique_payload()
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/login", json={"username": payload["email"], "password": payload["password"]})
    assert resp.status_code == 200


# ── OAuth2 form endpoint ──────────────────────────────────────────────────────

def test_login_form_success(client):
    payload = unique_payload()
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/token", data={
        "username": payload["username"],
        "password": payload["password"],
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_login_form_invalid(client):
    resp = client.post("/auth/token", data={"username": "nobody", "password": "BadPass99!"})
    assert resp.status_code == 401
