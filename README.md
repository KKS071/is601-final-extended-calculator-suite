# CalcApp — IS601 Final Project

[![CI](https://github.com/KKS071/is601-final-extended-calculator-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/KKS071/is601-final-extended-calculator-suite/actions)
[![Docker](https://img.shields.io/docker/v/kks59/is601-final-extended-calculator-suite?label=Docker%20Hub)](https://hub.docker.com/r/kks59/is601-final-extended-calculator-suite)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/KKS071/is601-final-extended-calculator-suite)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)

**IS601 — Python for Web API Development | NJIT — Spring 2026**  
**Student:** Kundan Singh

> A production-quality calculator web application built with **FastAPI**, **PostgreSQL**, **JWT authentication**, and full **BREAD** operations. Features a TailwindCSS dashboard, aggregated stats, profile management, and a three-stage GitHub Actions CI/CD pipeline that tests, scans, and deploys automatically.

- 🔗 **GitHub:** https://github.com/KKS071/is601-final-extended-calculator-suite
- 🐳 **Docker Hub:** https://hub.docker.com/r/kks59/is601-final-extended-calculator-suite
- 📖 **Swagger UI:** http://localhost:8000/docs (when running locally)

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Extra Features Beyond Requirements](#extra-features-beyond-requirements)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Local Setup](#local-setup)
7. [Docker Setup](#docker-setup)
8. [Environment Variables](#environment-variables)
9. [Running Tests](#running-tests)
10. [API Reference](#api-reference)
11. [CI/CD Pipeline](#cicd-pipeline)
12. [Security](#security)
13. [Alembic Migrations](#alembic-migrations)
14. [Links](#links)

---

## Overview

CalcApp is a full-stack web application that allows authenticated users to:

- Perform arithmetic calculations with **six operation types**, each supporting two or more operands
- Manage their full **calculation history** using BREAD operations (Browse, Read, Edit, Add, Delete)
- View **aggregated statistics** about their usage patterns
- **Update their profile** (name, email, username) and change their password
- Use a clean, responsive **TailwindCSS dashboard** served directly by FastAPI

The backend exposes a RESTful JSON API protected by JWT authentication. The frontend is built from Jinja2 templates with vanilla JavaScript that communicates with the API using `fetch()`. All sensitive data is validated at the schema level before reaching the database.

---

## Features

### BREAD Operations on Calculations

Every calculation supports the full BREAD lifecycle:

| Operation | Endpoint | Description |
|-----------|----------|-------------|
| **B**rowse | `GET /calculations` | List all calculations for the logged-in user, newest first |
| **R**ead | `GET /calculations/{id}` | Retrieve a single calculation by UUID |
| **E**dit | `PUT /calculations/{id}` | Update inputs or type; result is recomputed automatically |
| **A**dd | `POST /calculations` | Create a new calculation and store the result |
| **D**elete | `DELETE /calculations/{id}` | Remove a calculation permanently |

### Six Calculation Types

All types support **two or more operands** applied left-to-right:

| Type | Symbol | Example Inputs | Result |
|------|--------|---------------|--------|
| Addition | `+` | `[10, 5, 3]` | `18` |
| Subtraction | `−` | `[100, 30, 20]` | `50` |
| Multiplication | `×` | `[2, 3, 4]` | `24` |
| Division | `÷` | `[100, 5, 4]` | `5` |
| **Modulo** ✨ | `%` | `[10, 3]` | `1` |
| **Power** ✨ | `^` | `[2, 10]` | `1024` |

> **Modulo** and **Power** are extra operation types added beyond the basic four required operations.

---

## Extra Features Beyond Requirements

### 1 — Modulo Operation (`type: "modulo"`)

Computes the remainder of sequential modulo operations left-to-right. Raises a validation error if any divisor is zero. Useful for checking divisibility, cyclic indexing, and number theory exercises.

```json
POST /calculations
{ "type": "modulo", "inputs": [100, 7, 3] }
→ { "result": 2.0 }
```

### 2 — Power Operation (`type: "power"`)

Raises the first number to successive exponents left-to-right: `((a ^ b) ^ c) …`. Handles integer and floating-point exponents including fractional powers (e.g., square root via exponent `0.5`).

```json
POST /calculations
{ "type": "power", "inputs": [2, 10] }
→ { "result": 1024.0 }
```

### 3 — Aggregated Stats (`GET /calculations/stats`)

Returns a summary of the user's entire calculation history without requiring the client to load every record:

```json
{
  "total_count": 42,
  "by_type": { "addition": 18, "power": 10, "modulo": 7, "division": 7 },
  "average_operand_count": 2.4,
  "last_5": [ ... ]
}
```

| Field | Meaning |
|-------|---------|
| `total_count` | Total calculations ever created |
| `by_type` | Per-operation breakdown |
| `average_operand_count` | Average number of inputs per calculation — shows whether users tend to chain multiple values |
| `last_5` | The five most recently created calculations |

> **Why `average_operand_count` instead of `average_result`?** Averaging results across different operation types (e.g., additions and powers) produces a meaningless number. The average number of operands per calculation is a genuinely useful insight — it shows how complex the user's typical calculations are.

### 4 — Full Profile Management

Users can update their account information without re-registering:

- **`PUT /users/me`** — change first name, last name, email, and/or username. Conflict detection returns `409` if the new email or username is already taken.
- **`PUT /users/me/password`** — change password. The current password is verified before the new one is applied. New and confirmation must match. New password must differ from current.

### 5 — Password Visibility Toggle (Eye Icon)

Every password field across all pages (Login, Register, Profile) has an eye icon button. Clicking it toggles the input between `type="password"` and `type="text"` so users can verify what they have typed. The icon changes between open-eye and crossed-eye states. Built with two pre-rendered SVG icons and `style.display` toggling — no Tailwind class dependency, no external library.

### 6 — TailwindCSS Dashboard UI

The entire frontend uses Tailwind CSS (Play CDN) for a clean, modern look:

- **Stats banner** — four metric cards at the top of the dashboard (total calculations, average inputs per calculation, most-used operation type, and number of distinct types used)
- **Input pill preview** — as numbers are typed into the inputs field, they appear as coloured pill badges below the input in real time
- **Colour-coded operation badges** — each row in the history table shows a badge with a distinct colour per operation type
- **Responsive layout** — works on mobile, tablet, and desktop

### 7 — Welcome Banner with Full Name

The dashboard greeting shows the user's **First and Last Name** (e.g., "Welcome back, Kundan Singh!") rather than the username. The name is stored in `localStorage` on login and refreshed via `GET /users/me` on every dashboard load — so a profile name change is reflected immediately on the next visit without logging out.

### 8 — Enter-Key Support on All Forms

Every form field on every page supports submitting by pressing **Enter**, not just by clicking the button. This applies to: Login, Register, Dashboard (add calculation), Edit Calculation, Profile (account info and password change).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI 0.115 + Uvicorn |
| Language | Python 3.12 |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (single-table polymorphic inheritance) |
| Schema validation | Pydantic v2 |
| Authentication | JWT via `python-jose` + bcrypt via `passlib` |
| Frontend | Jinja2 templates, TailwindCSS Play CDN, vanilla JS |
| Testing | pytest, pytest-cov, pytest-playwright |
| E2E | Playwright + Chromium |
| CI/CD | GitHub Actions |
| Container | Docker (multi-stage build), docker-compose |
| Security scanning | Aqua Trivy |
| Settings | pydantic-settings |

---

## Project Structure

```
.
├── app/
│   ├── auth/
│   │   ├── dependencies.py     # JWT bearer dependency (get_current_active_user)
│   │   └── jwt.py              # Token creation, decoding, password hashing
│   ├── core/
│   │   └── config.py           # Settings via pydantic-settings (reads .env)
│   ├── models/
│   │   ├── calculation.py      # Calculation + six subclasses (polymorphic ORM)
│   │   └── user.py             # User model with register/authenticate helpers
│   ├── schemas/
│   │   ├── calculation.py      # CalculationBase, Response, Update, StatsResponse
│   │   ├── token.py            # Token, TokenData, TokenResponse
│   │   └── user.py             # UserCreate, UserResponse, UserUpdate, PasswordUpdate
│   ├── database.py             # Engine, SessionLocal, Base, get_db
│   ├── database_init.py        # init_db() / drop_db() helpers
│   ├── main.py                 # All FastAPI routes (auth, users, calculations, HTML)
│   └── operations.py           # Pure arithmetic: add, subtract, multiply, divide, modulo, power
├── docs/
│   └── REFLECTION.md           # Project reflection and lessons learned
├── static/
│   ├── css/style.css           # Operation badge colours + input pill styles
│   └── js/auth.js              # Navbar state + logout helper
├── templates/
│   ├── base.html               # Tailwind CDN, navbar, footer
│   ├── index.html              # Public landing page
│   ├── login.html              # Login form with password toggle
│   ├── register.html           # Registration form with password toggles
│   ├── dashboard.html          # Stats banner + add form + history table
│   ├── profile.html            # Profile update + password change forms
│   ├── view_calculation.html   # Read-only calculation detail
│   └── edit_calculation.html   # Edit form with all six operation types
├── tests/
│   ├── conftest.py             # SQLite StaticPool fixtures, test client, auth headers
│   ├── unit/
│   │   ├── test_operations.py      # Pure arithmetic function tests
│   │   ├── test_calculation_model.py  # Model.get_result() + factory tests
│   │   ├── test_schemas.py         # Pydantic validation tests
│   │   ├── test_jwt.py             # Token creation, decoding, expiry
│   │   └── test_user_model.py      # User helpers + verify_token
│   ├── integration/
│   │   ├── test_api_auth.py        # Register, login, form login endpoints
│   │   ├── test_api_calculations.py # BREAD + stats API tests
│   │   ├── test_api_routes.py      # HTML routes + profile + password endpoints
│   │   ├── test_calculation_model.py  # DB-backed model persistence
│   │   ├── test_user_model.py      # DB-backed User model tests
│   │   └── test_coverage_gaps.py   # Targeted tests for defensive code paths
│   └── e2e/
│       └── test_playwright.py  # Browser-based full user journey tests
├── .github/
│   └── workflows/ci.yml        # Test → Trivy scan → Docker build+push
├── .env.example                # Environment variable template
├── Dockerfile                  # Multi-stage production image
├── docker-compose.yml          # App + Postgres + test-Postgres
├── pytest.ini                  # Coverage config, asyncio mode, warning filters
└── requirements.txt            # All Python dependencies
```

---

## Local Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16 (running locally or via Docker)
- `createdb` CLI or a Postgres client

### Step-by-Step

```bash
# 1. Clone the repository
git clone https://github.com/KKS071/is601-final-extended-calculator-suite
cd is601-final-extended-calculator-suite

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Copy the environment template and fill in values
cp .env.example .env
# Open .env in your editor and set:
#   DATABASE_URL, TEST_DATABASE_URL, JWT_SECRET_KEY, JWT_REFRESH_SECRET_KEY

# 5. Create the databases
createdb fastapi_db
createdb fastapi_test_db

# 6. Start the development server (tables are auto-created on startup)
uvicorn app.main:app --reload
```

Open **http://localhost:8000** in your browser.  
Interactive API docs: **http://localhost:8000/docs**

---

## Docker Setup

```bash
# Build and start the full stack (app + Postgres + test-Postgres)
docker-compose up --build

# Run in the background
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (wipes DB data)
docker-compose down -v
```

| Service | URL |
|---------|-----|
| CalcApp | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Postgres (main) | localhost:5432 |
| Postgres (test) | localhost:5433 |

---

## Environment Variables

Copy `.env.example` to `.env` and set:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/fastapi_db` |
| `TEST_DATABASE_URL` | PostgreSQL connection for tests | `postgresql://postgres:postgres@localhost:5433/fastapi_test_db` |
| `JWT_SECRET_KEY` | Secret for signing access tokens | *(must change in production)* |
| `JWT_REFRESH_SECRET_KEY` | Secret for signing refresh tokens | *(must change in production)* |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `BCRYPT_ROUNDS` | bcrypt work factor | `12` |

> **Never commit a real `.env` file.** Use GitHub Secrets for CI/CD.

---

## Running Tests

### Unit and Integration Tests (no server required)

```bash
# Run all unit + integration tests with coverage (recommended)
TESTING=1 pytest tests/unit/ tests/integration/

# Verbose output
TESTING=1 pytest tests/unit/ tests/integration/ -v

# Unit tests only
TESTING=1 pytest tests/unit/

# Integration tests only
TESTING=1 pytest tests/integration/

# View the HTML coverage report
open htmlcov/index.html          # macOS
xdg-open htmlcov/index.html      # Linux
```

The `TESTING=1` flag prevents the FastAPI lifespan from trying to connect to PostgreSQL on startup — the test suite uses an in-memory SQLite database via SQLAlchemy's `StaticPool`, so no database server is required.

**Current result: 254 tests, 0 failures, 100% coverage.**

### End-to-End Tests (requires running server)

```bash
# Install the Playwright browser (one-time)
playwright install chromium

# Start the app (in a separate terminal)
uvicorn app.main:app --reload

# Run E2E tests
pytest tests/e2e/ --browser chromium

# Run headless (CI-friendly)
pytest tests/e2e/ --browser chromium --headless
```

E2E tests cover: register, login, dashboard BREAD operations (including modulo and power), profile page data loading, unauthenticated redirects, and logout.

### Test Architecture

| Layer | Tool | Database | Notes |
|-------|------|----------|-------|
| Unit | pytest | None | Pure Python logic only |
| Integration | pytest + TestClient | SQLite (in-memory) | Full HTTP stack, no external services |
| E2E | Playwright + Chromium | Real PostgreSQL | Full browser against live server |

---

## API Reference

All endpoints except `/auth/register`, `/auth/login`, and `/auth/token` require a valid `Authorization: Bearer <token>` header.

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/register` | ✗ | Create a new account |
| `POST` | `/auth/login` | ✗ | Login with JSON body — returns JWT tokens + user info |
| `POST` | `/auth/token` | ✗ | OAuth2 form login (used by Swagger UI Authorize button) |

### User Profile

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/users/me` | ✓ | Retrieve current user's profile |
| `PUT` | `/users/me` | ✓ | Update name / email / username |
| `PUT` | `/users/me/password` | ✓ | Change password (verifies current password first) |

### Calculations

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/calculations` | ✓ | Add a new calculation |
| `GET` | `/calculations` | ✓ | Browse all calculations (newest first) |
| `GET` | `/calculations/stats` | ✓ | Aggregated stats for current user |
| `GET` | `/calculations/{id}` | ✓ | Read a single calculation |
| `PUT` | `/calculations/{id}` | ✓ | Edit inputs/type; result recomputed |
| `DELETE` | `/calculations/{id}` | ✓ | Delete a calculation |

### Using Swagger UI

1. Open **http://localhost:8000/docs**
2. Click **POST /auth/register** → Try it out → fill in the body → Execute
3. Click the **🔒 Authorize** button at the top of the page
4. Enter your `username` and `password` → click **Authorize**
5. All protected routes now send your Bearer token automatically — click any locked route and try it out

### Request & Response Examples

**Create a power calculation:**
```json
POST /calculations
Content-Type: application/json
Authorization: Bearer <token>

{ "type": "power", "inputs": [2, 10] }

→ 201 Created
{
  "id": "3fa85f64-...",
  "type": "power",
  "inputs": [2.0, 10.0],
  "result": 1024.0,
  "user_id": "...",
  "created_at": "2026-05-06T22:00:00Z",
  "updated_at": "2026-05-06T22:00:00Z"
}
```

**Get stats:**
```json
GET /calculations/stats
Authorization: Bearer <token>

→ 200 OK
{
  "total_count": 15,
  "by_type": { "addition": 6, "power": 5, "modulo": 4 },
  "average_operand_count": 2.5,
  "last_5": [ ... ]
}
```

---

## CI/CD Pipeline

The pipeline is defined in `.github/workflows/ci.yml` and runs on every push or pull request to `main`/`master`.

### Stage 1 — Test

- Starts two PostgreSQL service containers (main DB + test DB)
- Installs all Python dependencies
- Runs `pytest --cov=app` with `TESTING=1`
- Uploads `coverage.xml` as a build artifact

### Stage 2 — Trivy Security Scan

- Runs after the test stage passes
- Scans the repository filesystem for **CRITICAL** and **HIGH** CVEs using `aquasecurity/trivy-action`
- `exit-code: 0` — findings are reported but do not block the build (some transitive vulnerabilities have no fix yet)

### Stage 3 — Docker Build & Push

- Runs on `main`/`master` only after both previous stages pass
- Builds a **multi-stage Docker image** (builder stage compiles wheels; final `python:3.12-slim` image contains only runtime dependencies)
- Pushes to Docker Hub: `kks59/is601-final-extended-calculator-suite:latest` and `kks59/is601-final-extended-calculator-suite:sha-<commit>`
- Runs a second Trivy scan against the pushed image

### Required GitHub Secrets (stored in the `production` environment)

| Secret | Used for |
|--------|---------|
| `DOCKERHUB_USERNAME` | Docker Hub login |
| `DOCKERHUB_TOKEN` | Docker Hub push authentication |
| `JWT_SECRET_KEY` | JWT signing in the test stage |
| `JWT_REFRESH_SECRET_KEY` | Refresh token signing in the test stage |

---

## Security

| Concern | Implementation |
|---------|---------------|
| Password storage | bcrypt via `passlib` — 12 rounds in production, 4 rounds in CI |
| Token security | JWT (HS256) signed with separate secrets for access and refresh tokens |
| Token expiry | Access tokens expire in 30 minutes; refresh tokens in 7 days |
| Input validation | Pydantic v2 validators enforce numeric types, minimum operand count, and zero-divisor checks before any DB operation |
| Data ownership | Every query filters on both `id` and `user_id` — users can only access their own calculations; returns `404` (not `403`) to avoid leaking record existence |
| Duplicate detection | Duplicate email/username on profile update returns `409 Conflict` |
| Password change | Current password is verified before applying a new one; new must differ from current |
| Docker security | Non-root `appuser` inside the container; `python:3.12-slim` base minimises CVE surface area |
| Secret management | All secrets in GitHub `production` environment; never in source code |

---

## Alembic Migrations

Tables are auto-created by SQLAlchemy on application startup via `Base.metadata.create_all()`. For production workflows that require controlled schema migrations, Alembic can be layered on top:

```bash
# 1. Initialize Alembic in the project root
alembic init alembic

# 2. Edit alembic.ini — set sqlalchemy.url to your DATABASE_URL
# 3. Edit alembic/env.py — import Base from app.models.user and set target_metadata

# 4. Generate the first migration from the current models
alembic revision --autogenerate -m "initial schema"

# 5. Apply migrations
alembic upgrade head

# 6. For future model changes
alembic revision --autogenerate -m "add new column"
alembic upgrade head

# 7. Roll back one migration
alembic downgrade -1
```

---

## Links

| Resource | URL |
|----------|-----|
| GitHub Repository | https://github.com/KKS071/is601-final-extended-calculator-suite |
| Docker Hub | https://hub.docker.com/r/kks59/is601-final-extended-calculator-suite |
| CI/CD Actions | https://github.com/KKS071/is601-final-extended-calculator-suite/actions |
| Swagger UI (local) | http://localhost:8000/docs |
| ReDoc (local) | http://localhost:8000/redoc |
