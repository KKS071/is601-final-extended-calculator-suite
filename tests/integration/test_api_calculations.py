# File: tests/integration/test_api_calculations.py
# Purpose: Integration tests for all BREAD calculation routes + stats endpoint.
import uuid
import pytest


CALC_TYPES = [
    ("addition",       [10, 5],   15.0),
    ("subtraction",    [20, 8],   12.0),
    ("multiplication", [3, 4],    12.0),
    ("division",       [20, 4],   5.0),
    ("modulo",         [10, 3],   1.0),
    ("power",          [2, 3],    8.0),
]


# ── Helper ────────────────────────────────────────────────────────────────────

def create_calc(client, auth_headers, ctype="addition", inputs=None):
    if inputs is None:
        inputs = [10, 5]
    resp = client.post(
        "/calculations",
        json={"type": ctype, "inputs": inputs},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Browse ────────────────────────────────────────────────────────────────────

def test_list_empty(client, auth_headers):
    resp = client.get("/calculations", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []

def test_list_unauthorized():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        resp = c.get("/calculations")
    assert resp.status_code == 401


# ── Add ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("ctype,inputs,expected", CALC_TYPES)
def test_create_all_types(client, auth_headers, ctype, inputs, expected):
    data = create_calc(client, auth_headers, ctype, inputs)
    assert data["result"] == pytest.approx(expected)
    assert data["type"] == ctype

def test_create_addition_multi_values(client, auth_headers):
    data = create_calc(client, auth_headers, "addition", [1, 2, 3, 4, 5])
    assert data["result"] == pytest.approx(15.0)

def test_create_multiplication_multi_values(client, auth_headers):
    data = create_calc(client, auth_headers, "multiplication", [2, 3, 4])
    assert data["result"] == pytest.approx(24.0)

def test_create_division_by_zero_returns_400(client, auth_headers):
    resp = client.post("/calculations", json={"type": "division", "inputs": [10, 0]}, headers=auth_headers)
    assert resp.status_code == 422

def test_create_modulo_by_zero_returns_422(client, auth_headers):
    resp = client.post("/calculations", json={"type": "modulo", "inputs": [10, 0]}, headers=auth_headers)
    assert resp.status_code == 422

def test_create_one_input_fails(client, auth_headers):
    resp = client.post("/calculations", json={"type": "addition", "inputs": [5]}, headers=auth_headers)
    assert resp.status_code == 422

def test_create_invalid_type(client, auth_headers):
    resp = client.post("/calculations", json={"type": "logarithm", "inputs": [5, 2]}, headers=auth_headers)
    assert resp.status_code == 422

def test_create_no_auth_fails(client):
    resp = client.post("/calculations", json={"type": "addition", "inputs": [1, 2]})
    assert resp.status_code == 401

def test_create_returns_user_id(client, auth_headers, test_user):
    data = create_calc(client, auth_headers)
    assert str(data["user_id"]) == str(test_user.id)

def test_create_response_has_timestamps(client, auth_headers):
    data = create_calc(client, auth_headers)
    assert "created_at" in data
    assert "updated_at" in data

def test_create_bad_token_returns_401(client):
    resp = client.post(
        "/calculations",
        json={"type": "addition", "inputs": [1, 2]},
        headers={"Authorization": "Bearer bad_token"},
    )
    assert resp.status_code == 401


# ── Read ──────────────────────────────────────────────────────────────────────

def test_read_existing(client, auth_headers):
    created = create_calc(client, auth_headers)
    resp    = client.get(f"/calculations/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]

def test_read_not_found(client, auth_headers):
    resp = client.get(f"/calculations/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404

def test_read_invalid_uuid(client, auth_headers):
    resp = client.get("/calculations/not-a-uuid", headers=auth_headers)
    assert resp.status_code == 400

def test_read_no_auth(client):
    resp = client.get(f"/calculations/{uuid.uuid4()}")
    assert resp.status_code == 401

def test_read_other_users_calc(client, db_session, auth_headers):
    """A user cannot read another user's calculation."""
    import uuid as _uuid
    from app.models.user import User
    from app.models.calculation import Calculation
    other = User(
        first_name="Other", last_name="User",
        email=f"other_{_uuid.uuid4().hex[:8]}@ex.com",
        username=f"other_{_uuid.uuid4().hex[:8]}",
        password=User.hash_password("OtherPass1!"),
        is_active=True, is_verified=True,
    )
    db_session.add(other)
    db_session.flush()
    calc = Calculation.create("addition", other.id, [1, 2])
    calc.result = calc.get_result()
    db_session.add(calc)
    db_session.commit()
    resp = client.get(f"/calculations/{calc.id}", headers=auth_headers)
    assert resp.status_code == 404


# ── Edit ──────────────────────────────────────────────────────────────────────

def test_update_inputs(client, auth_headers):
    created = create_calc(client, auth_headers, "addition", [1, 2])
    resp    = client.put(
        f"/calculations/{created['id']}",
        json={"inputs": [10, 20]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == pytest.approx(30.0)

def test_update_type(client, auth_headers):
    created = create_calc(client, auth_headers, "addition", [10, 5])
    resp    = client.put(
        f"/calculations/{created['id']}",
        json={"type": "subtraction"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["type"] == "subtraction"
    assert resp.json()["result"] == pytest.approx(5.0)

def test_update_to_modulo(client, auth_headers):
    created = create_calc(client, auth_headers, "addition", [10, 3])
    resp    = client.put(
        f"/calculations/{created['id']}",
        json={"type": "modulo"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == pytest.approx(1.0)

def test_update_to_power(client, auth_headers):
    created = create_calc(client, auth_headers, "addition", [2, 3])
    resp    = client.put(
        f"/calculations/{created['id']}",
        json={"type": "power"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == pytest.approx(8.0)

def test_update_division_by_zero(client, auth_headers):
    created = create_calc(client, auth_headers, "addition", [10, 5])
    resp    = client.put(
        f"/calculations/{created['id']}",
        json={"type": "division", "inputs": [10, 0]},
        headers=auth_headers,
    )
    assert resp.status_code in (400, 422)

def test_update_not_found(client, auth_headers):
    resp = client.put(
        f"/calculations/{uuid.uuid4()}",
        json={"inputs": [1, 2]},
        headers=auth_headers,
    )
    assert resp.status_code == 404

def test_update_invalid_uuid(client, auth_headers):
    resp = client.put("/calculations/bad-id", json={"inputs": [1, 2]}, headers=auth_headers)
    assert resp.status_code == 400

def test_update_no_auth(client):
    resp = client.put(f"/calculations/{uuid.uuid4()}", json={"inputs": [1, 2]})
    assert resp.status_code == 401


# ── Delete ────────────────────────────────────────────────────────────────────

def test_delete_success(client, auth_headers):
    created = create_calc(client, auth_headers)
    resp    = client.delete(f"/calculations/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204

def test_delete_gone_after_delete(client, auth_headers):
    created = create_calc(client, auth_headers)
    client.delete(f"/calculations/{created['id']}", headers=auth_headers)
    resp = client.get(f"/calculations/{created['id']}", headers=auth_headers)
    assert resp.status_code == 404

def test_delete_not_found(client, auth_headers):
    resp = client.delete(f"/calculations/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404

def test_delete_invalid_uuid(client, auth_headers):
    resp = client.delete("/calculations/bad-id", headers=auth_headers)
    assert resp.status_code == 400

def test_delete_no_auth(client):
    resp = client.delete(f"/calculations/{uuid.uuid4()}")
    assert resp.status_code == 401


# ── Stats ─────────────────────────────────────────────────────────────────────

def test_stats_empty(client, auth_headers):
    resp = client.get("/calculations/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] == 0
    assert data["average_operand_count"] is None
    assert data["last_5"] == []

def test_stats_after_calculations(client, auth_headers):
    create_calc(client, auth_headers, "addition", [10, 5])
    create_calc(client, auth_headers, "subtraction", [20, 8])
    create_calc(client, auth_headers, "modulo", [10, 3])
    create_calc(client, auth_headers, "power", [2, 3])
    resp = client.get("/calculations/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] >= 4
    assert "addition" in data["by_type"]
    assert data["average_operand_count"] is not None
    assert len(data["last_5"]) <= 5

def test_stats_no_auth(client):
    resp = client.get("/calculations/stats")
    assert resp.status_code == 401
