# File: tests/e2e/test_playwright.py
# Purpose: Playwright end-to-end tests.
#
# Pattern for tests that need a pre-authenticated page:
#   1. page.goto(BASE_URL + "/")   — home page, no JS redirect
#   2. page.evaluate(...)          — set localStorage token
#   3. page.goto(BASE_URL + "/X")  — navigate to protected page
#
# Tests that call localStorage.clear() must also start from a real
# page (not about:blank) because localStorage is origin-scoped.
#
# Run:  pytest tests/e2e/ --browser chromium
import uuid
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8001"
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


def _register_and_login(user: dict) -> str:
    """Helper: register + login via API, return access token."""
    import httpx
    httpx.post(f"{BASE_URL}/auth/register", json={
        "first_name":       user["first_name"],
        "last_name":        user["last_name"],
        "email":            user["email"],
        "username":         user["username"],
        "password":         PASSWORD,
        "confirm_password": PASSWORD,
    })
    resp = httpx.post(f"{BASE_URL}/auth/login",
                         json={"username": user["username"], "password": PASSWORD})
    return resp.json()["access_token"]


def _set_token(page: Page, token: str, username: str = "") -> None:
    """Navigate to the home page and set the auth token in localStorage.

    Must navigate to a real page first — localStorage is unavailable on
    about:blank (raises a SecurityError in Playwright).
    """
    page.goto(f"{BASE_URL}/")
    page.evaluate(f"""() => {{
        localStorage.setItem('access_token', '{token}');
        localStorage.setItem('username', '{username}');
    }}""")


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
    page.wait_for_url(f"{BASE_URL}/login", timeout=8000)
    expect(page).to_have_url(f"{BASE_URL}/login")


@pytest.mark.e2e
def test_register_password_mismatch(page: Page):
    user = unique_user()
    page.goto(f"{BASE_URL}/register")

    page.fill("#first_name",       user["first_name"])
    page.fill("#last_name",        user["last_name"])
    page.fill("#email",            user["email"])
    page.fill("#username",         user["username"])
    page.fill("#password",         "SecureE2E123!")
    page.fill("#confirm_password", "DifferentPass1!")
    page.click("#register-btn")

    error_el = page.locator("#error-msg")
    expect(error_el).to_be_visible()
    expect(error_el).to_contain_text("match")


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_login_flow(page: Page):
    user  = unique_user()
    _register_and_login(user)           # register via API first

    page.goto(f"{BASE_URL}/login")
    page.fill("#username", user["username"])
    page.fill("#password", PASSWORD)
    page.click("#login-btn")
    page.wait_for_url(f"{BASE_URL}/dashboard", timeout=8000)
    expect(page).to_have_url(f"{BASE_URL}/dashboard")


@pytest.mark.e2e
def test_login_invalid_credentials(page: Page):
    page.goto(f"{BASE_URL}/login")
    page.fill("#username", "nonexistent_user_xyz")
    page.fill("#password", "WrongPass99!")
    page.click("#login-btn")

    error_el = page.locator("#error-msg")
    expect(error_el).to_be_visible()


# ── Dashboard — unauthenticated redirect ─────────────────────────────────────

@pytest.mark.e2e
def test_dashboard_redirects_unauthenticated(page: Page):
    # Must be on a real page before touching localStorage (not about:blank)
    page.goto(f"{BASE_URL}/")
    page.evaluate("localStorage.clear()")

    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_url(f"{BASE_URL}/login", timeout=8000)
    expect(page).to_have_url(f"{BASE_URL}/login")


# ── Dashboard — add calculations ──────────────────────────────────────────────

def _open_dashboard(page: Page, user: dict) -> None:
    """Register, login, inject token, then open the dashboard."""
    token = _register_and_login(user)
    # Set token on home page (no redirect), then navigate to dashboard
    _set_token(page, token, user["username"])
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_selector("#calculate-btn", timeout=8000)


@pytest.mark.e2e
def test_add_calculation(page: Page):
    user = unique_user()
    _open_dashboard(page, user)

    page.select_option("#operation", "addition")
    page.fill("#inputs-field", "10, 5")
    page.click("#calculate-btn")

    result_box = page.locator("#result-box")
    expect(result_box).to_be_visible(timeout=8000)
    expect(page.locator("#result-value")).to_contain_text("15")


@pytest.mark.e2e
def test_add_modulo_calculation(page: Page):
    user = unique_user()
    _open_dashboard(page, user)

    page.select_option("#operation", "modulo")
    page.fill("#inputs-field", "10, 3")
    page.click("#calculate-btn")

    result_box = page.locator("#result-box")
    expect(result_box).to_be_visible(timeout=8000)
    expect(page.locator("#result-value")).to_contain_text("1")


@pytest.mark.e2e
def test_add_power_calculation(page: Page):
    user = unique_user()
    _open_dashboard(page, user)

    page.select_option("#operation", "power")
    page.fill("#inputs-field", "2, 3")
    page.click("#calculate-btn")

    result_box = page.locator("#result-box")
    expect(result_box).to_be_visible(timeout=8000)
    expect(page.locator("#result-value")).to_contain_text("8")


# ── Profile — unauthenticated redirect ───────────────────────────────────────

@pytest.mark.e2e
def test_profile_page_redirects_unauthenticated(page: Page):
    # Must be on a real page before touching localStorage
    page.goto(f"{BASE_URL}/")
    page.evaluate("localStorage.clear()")

    page.goto(f"{BASE_URL}/profile")
    page.wait_for_url(f"{BASE_URL}/login", timeout=8000)
    expect(page).to_have_url(f"{BASE_URL}/login")


# ── Profile — loads user data ─────────────────────────────────────────────────

@pytest.mark.e2e
def test_profile_page_loads_data(page: Page):
    user  = unique_user()
    token = _register_and_login(user)

    # Set token on home page, then navigate to profile
    _set_token(page, token, user["username"])
    page.goto(f"{BASE_URL}/profile")

    # The profile JS makes an async GET /users/me to populate fields.
    # Use to_have_value() which polls until the value arrives (not just the element).
    expect(page.locator("#username")).to_have_value(user["username"], timeout=8000)


# ── Logout ────────────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_logout(page: Page):
    user  = unique_user()
    token = _register_and_login(user)

    # Set token on home page, then navigate to dashboard
    _set_token(page, token, user["username"])
    page.goto(f"{BASE_URL}/dashboard")
    page.wait_for_selector("#nav-logout", timeout=8000)
    page.click("#nav-logout")
    page.wait_for_url(f"{BASE_URL}/login", timeout=8000)
    expect(page).to_have_url(f"{BASE_URL}/login")
