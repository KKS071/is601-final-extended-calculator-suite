# Reflection — IS601 Final Project - Spring 2026

**CalcApp Extended Calculator Suite**  
**Student:** **Kundan Singh** | **Course:** IS601 — Python for Web API Development | **School:** NJIT

---

## What Was Built

This project is a full-stack web application that lets authenticated users perform multi-value arithmetic calculations and manage their history. At its core is a FastAPI backend exposing a RESTful API with six operation types — addition, subtraction, multiplication, division, **modulo** (extra feature), and **power** (extra feature) — each supporting more than two operands.

Beyond the calculations themselves, the app implements:
- Full BREAD (Browse, Read, Edit, Add, Delete) on the `/calculations` resource
- JWT-based authentication with access and refresh tokens
- Per-user calculation history with aggregated stats (total count, top calculation-type, average number of inputs per calculation, types of operation performed.)
- User profile management (update name / email / username, and a dedicated password-change flow)
- A TailwindCSS-styled frontend served by Jinja2 templates

---

## How Backend, DB, and Frontend Integrate

The backend is a single FastAPI app (`app/main.py`) that mounts static files, serves Jinja2 HTML templates for page routes, and exposes JSON API routes for auth and BREAD operations.

**Database layer:** SQLAlchemy ORM with single-table polymorphic inheritance — one `calculations` table with a `type` discriminator column. Each operation type (`Addition`, `Subtraction`, etc.) is a Python subclass that implements `get_result()`. This keeps the schema simple while allowing clean OOP dispatch. The `User` model owns a `calculations` relationship with cascade delete.

**Frontend integration:** The HTML templates are mostly static shells — all dynamic behaviour happens in inline JavaScript that calls the JSON API using `fetch()`. The JWT access token is stored in `localStorage` and sent as a `Bearer` header. The navbar updates itself on `DOMContentLoaded` based on token presence.

**Separation of concerns:** Pydantic schemas handle validation before any business logic runs. SQLAlchemy models own DB persistence. `app/operations.py` contains pure arithmetic functions that are independently testable without any framework.

---

## Testing Strategy

I aimed for 100% coverage using three layers:

**Unit tests** (`tests/unit/`) test pure logic with zero I/O — arithmetic functions, model `get_result()` methods, Pydantic schema validation rules, JWT utility functions, and User model helpers. These are fast (< 1 second) and catch regressions in business logic.

**Integration tests** (`tests/integration/`) use FastAPI's `TestClient` with a real PostgreSQL test database. A transactional fixture wraps each test in a savepoint that rolls back after the test, keeping tests isolated without recreating tables. These tests cover every API endpoint — happy paths, error paths, authorization failures, and edge cases like division by zero or invalid UUIDs.

**E2E tests** (`tests/e2e/`) use Playwright to drive a real Chromium browser against a live server. They test full user journeys: register → login → add calculations → view → edit → delete → logout. These run separately (excluded from CI coverage collection) to avoid requiring a running server in the test job.

**Negative testing** is present throughout: wrong passwords, missing tokens, invalid UUIDs, password mismatch while changing, new password same as old one, password too small, authentication denied on wrong password or username, duplicate emails, too-few inputs, zero divisors, and unauthorized access to other users' data.

---

## CI/CD and DevOps

The GitHub Actions pipeline (`ci.yml`) has three jobs that run sequentially:

1. **Test:** Spins up two PostgreSQL service containers, installs dependencies, and runs `pytest --cov`. Uploads coverage XML as an artifact.
2. **Trivy:** Runs `aquasecurity/trivy-action` on the filesystem to scan for CRITICAL and HIGH CVEs in dependencies. Non-blocking (`exit-code: 0`) to avoid breaking the build on unresolvable transitive vulnerabilities, while still surfacing findings in the Actions log.
3. **Docker:** Builds a multi-stage Docker image (builder stage installs wheels, final stage copies only the wheels and app code), pushes to `kks59/is601-final-extended-calculator-suite` on Docker Hub, then runs a second Trivy scan on the pushed image.

The Docker image uses a non-root user (`appuser`) and a `HEALTHCHECK` instruction that pings `/health`. Secrets (`DOCKERHUB_TOKEN`, `DOCKERHUB_USERNAME`) are stored in a GitHub `production` environment and never appear in logs.

---

## Security Practices

- **Passwords:** bcrypt-hashed via `passlib` (12 rounds in production, 4 rounds in CI for speed). Plain-text passwords are never stored or returned in responses.
- **JWT:** Access tokens expire in 30 minutes; refresh tokens in 7 days. Tokens are signed with separate secrets. Expired and malformed tokens return 401 with `WWW-Authenticate: Bearer`.
- **Input validation:** Pydantic schemas enforce numeric types, minimum input count, and operation-specific constraints (e.g., no zero divisor). Invalid UUIDs return 400 before hitting the database.
- **Data isolation:** Every calculation query filters on both `id` and `user_id`. A user cannot read, edit, or delete another user's calculations — a 404 is returned rather than 403 to avoid leaking record existence.
- **Profile updates:** Duplicate email/username conflicts return 409. The password-change endpoint verifies the current password before applying the new one.
- **Docker:** Non-root user, minimal final image (`python:3.12-slim`), no dev dependencies in the container.

---

## Lessons Learned

**SQLAlchemy polymorphic inheritance** is elegant for the calculator use case — each operation is self-contained, the factory pattern makes creation clean, and the single table keeps queries simple. The trade-off is that adding a new operation type requires a code change, not just a data change. For a richer math engine, a strategy pattern or plugin architecture would scale better.

**Transactional test fixtures** (savepoint + rollback) were a game-changer compared to creating/dropping tables per test. Tests became much faster and fully isolated, which enabled running 100+ tests against a real Postgres database without slowdown.

**Pydantic v2 validators** (`model_validator`, `field_validator`) provide a clean single place for cross-field rules (password match, zero divisor check). The validator runs before any model method, so invalid data never reaches the database layer.

**Playwright E2E tests** revealed frontend bugs that API tests couldn't catch — in particular, the `localStorage` token guard redirecting before the page loaded. Keeping E2E tests in a separate `tests/e2e/` directory and excluding them from the CI coverage run (they need a live server) is a practical pattern I'll carry forward.

**Docker multi-stage builds** significantly reduced image size by leaving the compiler toolchain in the builder stage. This also speeds up push/pull and reduces the Trivy CVE surface area.

Overall, this project connected all the dots between API design, ORM modelling, JWT security, frontend integration, testing strategy, and CI/CD automation — and showed how each layer depends on and validates the others.
