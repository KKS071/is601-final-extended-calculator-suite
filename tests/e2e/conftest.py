# File: tests/e2e/conftest.py
# Purpose: Session-scoped fixture that starts a real uvicorn server on
#          http://127.0.0.1:8000 before any E2E test runs, then tears it down.
#
# Why a live server instead of TestClient?
#   Playwright drives a real Chromium browser which needs an actual HTTP port.
#   TestClient is in-process only; it cannot be reached by an external process.
#
# How it coexists with unit/integration tests:
#   - Unit/integration tests use an in-memory SQLite DB via dependency override.
#   - This server uses the real PostgreSQL DATABASE_URL from settings.
#   - TESTING=1 is set globally by tests/conftest.py so the FastAPI lifespan
#     skips its own create_all(); we create tables here manually instead.
import threading
import time

import httpx
import pytest
import uvicorn
from sqlalchemy import create_engine

from app.core.config import get_settings
from app.database import Base

_BASE_URL = "http://127.0.0.1:8000"
_PORT     = 8000
_TIMEOUT  = 20  # seconds to wait for the server to become healthy


@pytest.fixture(scope="session", autouse=True)
def live_server():
    """Start a real uvicorn server for the entire E2E test session."""
    settings = get_settings()

    # Create PostgreSQL tables for the live server (lifespan skips this when
    # TESTING=1 is set, so we do it explicitly here).
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    # Configure uvicorn — error-level logging keeps CI output clean.
    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=_PORT,
        log_level="error",
        loop="asyncio",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Poll /health until the server is ready or the timeout expires.
    deadline = time.monotonic() + _TIMEOUT
    started  = False
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(f"{_BASE_URL}/health", timeout=1.0)
            if resp.status_code == 200:
                started = True
                break
        except Exception:
            pass
        time.sleep(0.25)

    if not started:
        server.should_exit = True
        thread.join(timeout=5)
        pytest.fail(f"Live server did not become healthy within {_TIMEOUT}s")

    yield  # ── E2E tests run here ──

    # Graceful shutdown.
    server.should_exit = True
    thread.join(timeout=10)

    # Drop tables so each CI run starts with a clean slate.
    cleanup = create_engine(settings.DATABASE_URL)
    Base.metadata.drop_all(bind=cleanup)
    cleanup.dispose()
