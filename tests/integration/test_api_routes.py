# File: tests/integration/test_api_routes.py
# Purpose: Integration tests for HTML page routes, health endpoint, profile, and password.
import uuid
import pytest


# ── Health / HTML ──────────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "CalcApp" in resp.text

def test_login_page(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "login" in resp.text.lower() or "sign" in resp.text.lower()

def test_register_page(client):
    resp = client.get("/register")
    assert resp.status_code == 200
    assert "register" in resp.text.lower() or "create" in resp.text.lower()

def test_dashboard_page(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200

def test_profile_page(client):
    resp = client.get("/profile")
    assert resp.status_code == 200

def test_view_page(client):
    resp = client.get(f"/dashboard/view/{uuid.uuid4()}")
    assert resp.status_code == 200

def test_edit_page(client):
    resp = client.get(f"/dashboard/edit/{uuid.uuid4()}")
    assert resp.status_code == 200


# ── /users/me ─────────────────────────────────────────────────────────────────

def test_get_me_success(client, auth_headers, test_user):
    resp = client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert "password" not in data

def test_get_me_no_auth(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401

def test_get_me_bad_token(client):
    resp = client.get("/users/me", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401


# ── PUT /users/me ─────────────────────────────────────────────────────────────

def test_update_profile_first_name(client, auth_headers):
    resp = client.put("/users/me", json={"first_name": "Updated"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Updated"

def test_update_profile_email(client, auth_headers):
    new_email = f"updated_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.put("/users/me", json={"email": new_email}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == new_email

def test_update_profile_username(client, auth_headers):
    new_un = f"newun_{uuid.uuid4().hex[:8]}"
    resp = client.put("/users/me", json={"username": new_un}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == new_un

def test_update_profile_no_fields_returns_400(client, auth_headers):
    resp = client.put("/users/me", json={}, headers=auth_headers)
    assert resp.status_code == 400

def test_update_profile_duplicate_email_returns_409(client, auth_headers, db_session):
    from app.models.user import User
    other = User(
        first_name="Other", last_name="Person",
        email=f"taken_{uuid.uuid4().hex[:8]}@example.com",
        username=f"taken_{uuid.uuid4().hex[:8]}",
        password=User.hash_password("TakenPass1!"),
        is_active=True, is_verified=True,
    )
    db_session.add(other)
    db_session.commit()
    resp = client.put("/users/me", json={"email": other.email}, headers=auth_headers)
    assert resp.status_code == 409

def test_update_profile_invalid_email(client, auth_headers):
    resp = client.put("/users/me", json={"email": "not-an-email"}, headers=auth_headers)
    assert resp.status_code == 422

def test_update_profile_no_auth(client):
    resp = client.put("/users/me", json={"first_name": "X"})
    assert resp.status_code == 401


# ── PUT /users/me/password ────────────────────────────────────────────────────

def test_change_password_success(client, auth_headers):
    resp = client.put(
        "/users/me/password",
        json={
            "current_password":     "TestPass123!",
            "new_password":         "NewSecure456!",
            "confirm_new_password": "NewSecure456!",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Password updated successfully"

def test_change_password_wrong_current(client, auth_headers):
    resp = client.put(
        "/users/me/password",
        json={
            "current_password":     "WrongPass999!",
            "new_password":         "NewSecure456!",
            "confirm_new_password": "NewSecure456!",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400

def test_change_password_mismatch_422(client, auth_headers):
    resp = client.put(
        "/users/me/password",
        json={
            "current_password":     "TestPass123!",
            "new_password":         "NewPass456!",
            "confirm_new_password": "DifferentPass1!",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422

def test_change_password_same_as_current_422(client, auth_headers):
    resp = client.put(
        "/users/me/password",
        json={
            "current_password":     "TestPass123!",
            "new_password":         "TestPass123!",
            "confirm_new_password": "TestPass123!",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422

def test_change_password_no_auth(client):
    resp = client.put(
        "/users/me/password",
        json={
            "current_password":     "TestPass123!",
            "new_password":         "NewPass456!",
            "confirm_new_password": "NewPass456!",
        },
    )
    assert resp.status_code == 401
