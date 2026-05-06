# File: tests/e2e/test_playwright.py
# Purpose: Playwright end-to-end tests — register, login, BREAD, profile, logout.
#
# Run with:
#   pytest tests/e2e/ --browser chromium --headed
# or headless (CI):
#   pytest tests/e2e/ --browser chromium
#
# Requires: pip install playwright pytest-playwright && playwright install chromium
import uuid
import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8000"
PASSWORD = "SecureE2E123!"


def unique_user():
    suffix = uuid.uuid4().hex[:8]
    return {
        "first_name": "E2E",
        "last_name":  "User",
        "email":      f"e2e_{suffix}@example.com",
        "username":   f"e2e_{suffix}",
        "password":   PASSWORD,
    }


# ── Register ──────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_register_flow(page: Page):
    user = unique_user()
    page.goto(f"{BASE_URL}/register")

    page.fill("#first_name", user["first_name"])
    page.fill("#last_name",  user["last_name"])
    page.fill("#email",      user["email"])
    page.fill("#username",   user["username"])
    page.fill("#password",           PASSWORD)
    page.fill("#confirm_password",   PASSWORD)

    page.click("#register-btn")
    page.wait_for_url(f"{BASE_URL}/login", timeout=5000)
    expect(page).to_have_url(f"{BASE_URL}/login")


@pytest.mark.e2e
def test_register_password_mismatch(page: Page):
    user = unique_user()
    page.goto(f"{BASE_URL}/register")
    page.fill("#first_name", user["first_name"])
    page.fill("#last_name",  user["last_name"])
    page.fill("#email",      user["email"])
    page.fill("#username",   user["username"])
    page.fill("#password",         "SecureE2E123!")
    page.fill("#confirm_password", "DifferentPass1!")
    page.click("#register-btn")

    # Should show an error, not redirect
    error_el = page.locator("#error-msg")
    expect(error_el).to_be_visible()
    expect(error_el).to_contain_text("match")


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_login_flow(page: Page):
    user = unique_user()
    # Register first via API
    import requests
    requests.post(f"{BASE_URL}/auth/register", json={
        "first_name":       user["first_name"],
        "last_name":        user["last_name"],
        "email":            user["email"],
        "username":         user["username"],
        "password":         PASSWORD,
        "confirm_password": PASSWORD,
    })

    page.goto(f"{BASE_URL}/login")
    page.fill("#username", user["username"])
    page.fill("#password", PASSWORD)
    page.click("#login-btn")
    page.wait_for_url(f"{BASE_URL}/dashboard", timeout=5000)
    expect(page).to_have_url(f"{BASE_URL}/dashboard")


@pytest.mark.e2e
def test_login_invalid_credentials(page: Page):
    page.goto(f"{BASE_URL}/login")
    page.fill("#username", "nonexistent_user_xyz")
    page.fill("#password", "WrongPass99!")
    page.click("#login-btn")

    error_el = page.locator("#error-msg")
    expect(error_el).to_be_visible()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_dashboard_redirects_unauthenticated(page: Page):
    page.evaluate("localStorage.clear()")
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_url(f"{BASE_URL}/login", timeout=5000)
    expect(page).to_have_url(f"{BASE_URL}/login")


@pytest.mark.e2e
def test_add_calculation(page: Page):
    user = unique_user()
    import requests
    requests.post(f"{BASE_URL}/auth/register", json={
        "first_name": user["first_name"], "last_name": user["last_name"],
        "email": user["email"],     "username": user["username"],
        "password": PASSWORD,       "confirm_password": PASSWORD,
    })
    login_resp = requests.post(f"{BASE_URL}/auth/login",
                               json={"username": user["username"], "password": PASSWORD})
    token = login_resp.json()["access_token"]

    page.goto(f"{BASE_URL}/dashboard")
    page.evaluate(f"""() => {{
        localStorage.setItem('access_token', '{token}');
        localStorage.setItem('username', '{user["username"]}');
    }}""")
    page.reload()
    page.wait_for_selector("#calculate-btn", timeout=5000)

    page.select_option("#operation", "addition")
    page.fill("#inputs-field", "10, 5")
    page.click("#calculate-btn")

    result_box = page.locator("#result-box")
    expect(result_box).to_be_visible(timeout=5000)
    expect(page.locator("#result-value")).to_contain_text("15")


@pytest.mark.e2e
def test_add_modulo_calculation(page: Page):
    user = unique_user()
    import requests
    requests.post(f"{BASE_URL}/auth/register", json={
        "first_name": user["first_name"], "last_name": user["last_name"],
        "email": user["email"],     "username": user["username"],
        "password": PASSWORD,       "confirm_password": PASSWORD,
    })
    login_resp = requests.post(f"{BASE_URL}/auth/login",
                               json={"username": user["username"], "password": PASSWORD})
    token = login_resp.json()["access_token"]

    page.goto(f"{BASE_URL}/dashboard")
    page.evaluate(f"""() => {{
        localStorage.setItem('access_token', '{token}');
        localStorage.setItem('username', '{user["username"]}');
    }}""")
    page.reload()
    page.wait_for_selector("#calculate-btn", timeout=5000)

    page.select_option("#operation", "modulo")
    page.fill("#inputs-field", "10, 3")
    page.click("#calculate-btn")

    result_box = page.locator("#result-box")
    expect(result_box).to_be_visible(timeout=5000)
    expect(page.locator("#result-value")).to_contain_text("1")


@pytest.mark.e2e
def test_add_power_calculation(page: Page):
    user = unique_user()
    import requests
    requests.post(f"{BASE_URL}/auth/register", json={
        "first_name": user["first_name"], "last_name": user["last_name"],
        "email": user["email"],     "username": user["username"],
        "password": PASSWORD,       "confirm_password": PASSWORD,
    })
    login_resp = requests.post(f"{BASE_URL}/auth/login",
                               json={"username": user["username"], "password": PASSWORD})
    token = login_resp.json()["access_token"]

    page.goto(f"{BASE_URL}/dashboard")
    page.evaluate(f"""() => {{
        localStorage.setItem('access_token', '{token}');
        localStorage.setItem('username', '{user["username"]}');
    }}""")
    page.reload()
    page.wait_for_selector("#calculate-btn", timeout=5000)

    page.select_option("#operation", "power")
    page.fill("#inputs-field", "2, 3")
    page.click("#calculate-btn")

    result_box = page.locator("#result-box")
    expect(result_box).to_be_visible(timeout=5000)
    expect(page.locator("#result-value")).to_contain_text("8")


# ── Profile page ──────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_profile_page_redirects_unauthenticated(page: Page):
    page.evaluate("localStorage.clear()")
    page.goto(f"{BASE_URL}/profile")
    page.wait_for_url(f"{BASE_URL}/login", timeout=5000)
    expect(page).to_have_url(f"{BASE_URL}/login")


@pytest.mark.e2e
def test_profile_page_loads_data(page: Page):
    user = unique_user()
    import requests
    requests.post(f"{BASE_URL}/auth/register", json={
        "first_name": user["first_name"], "last_name": user["last_name"],
        "email": user["email"],     "username": user["username"],
        "password": PASSWORD,       "confirm_password": PASSWORD,
    })
    login_resp = requests.post(f"{BASE_URL}/auth/login",
                               json={"username": user["username"], "password": PASSWORD})
    token = login_resp.json()["access_token"]

    page.goto(f"{BASE_URL}/profile")
    page.evaluate(f"() => localStorage.setItem('access_token', '{token}')")
    page.reload()
    page.wait_for_selector("#username", timeout=5000)

    val = page.input_value("#username")
    assert val == user["username"]


# ── Logout ────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_logout(page: Page):
    user = unique_user()
    import requests
    requests.post(f"{BASE_URL}/auth/register", json={
        "first_name": user["first_name"], "last_name": user["last_name"],
        "email": user["email"],     "username": user["username"],
        "password": PASSWORD,       "confirm_password": PASSWORD,
    })
    login_resp = requests.post(f"{BASE_URL}/auth/login",
                               json={"username": user["username"], "password": PASSWORD})
    token = login_resp.json()["access_token"]

    page.goto(f"{BASE_URL}/dashboard")
    page.evaluate(f"() => localStorage.setItem('access_token', '{token}')")
    page.reload()
    page.wait_for_selector("#nav-logout", timeout=5000)
    page.click("#nav-logout")
    page.wait_for_url(f"{BASE_URL}/login", timeout=5000)
    expect(page).to_have_url(f"{BASE_URL}/login")
