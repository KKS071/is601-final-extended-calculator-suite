# CalcApp — IS601 Final Project

**IS601 — Python for Web API Development | NJIT**

A production-quality calculator web application built with FastAPI, PostgreSQL, JWT authentication, and full BREAD operations. Deployed via Docker with an automated GitHub Actions CI/CD pipeline.

- 🔗 **GitHub:** https://github.com/KKS071/is601-final-extended-calculator-suite
- 🐳 **Docker Hub:** https://hub.docker.com/r/kks59/is601-final-extended-calculator-suite

---

## Overview

CalcApp lets authenticated users create, browse, read, edit, and delete calculations with six operation types. It also tracks per-user history statistics and exposes full profile management (name, email, username, and password change).

---

## Tech Stack

| Layer        | Technology                            |
|--------------|---------------------------------------|
| Backend      | FastAPI 0.115, Python 3.12            |
| Database     | PostgreSQL 16 + SQLAlchemy 2.0        |
| Auth         | JWT (python-jose) + bcrypt (passlib)  |
| Validation   | Pydantic v2                           |
| Frontend     | Jinja2 templates + TailwindCSS (CDN)  |
| Testing      | pytest, pytest-cov, Playwright        |
| CI/CD        | GitHub Actions + Docker Hub           |
| Security     | Trivy vulnerability scanning          |
| Container    | Docker (multi-stage), docker-compose  |

---

## Features

### Core BREAD Operations
All six operation types support multiple inputs (e.g., `[10, 5, 3]`):

| Type           | Example          | Result |
|----------------|------------------|--------|
| Addition       | `[10, 5, 3]`     | 18     |
| Subtraction    | `[100, 30, 20]`  | 50     |
| Multiplication | `[2, 3, 4]`      | 24     |
| Division       | `[100, 5, 4]`    | 5      |
| **Modulo** ✨  | `[10, 3]`        | 1      |
| **Power** ✨   | `[2, 10]`        | 1024   |

### Extra Features

1. **Aggregated Stats (`GET /calculations/stats`)** — total count, top calculation-type, average number of inputs per calculation, types of operation performed.
2. **Profile Management (`PUT /users/me`)** — update name, email, or username.
3. **Password Change (`PUT /users/me/password`)** — verifies current password before applying new one.
4. **Added additional calculation types - Power & Modulo**
5. **Optionally Allows users to view entered values in the password field by clicking on Eye Icon**

---

## Setup Instructions

### Prerequisites
- Python 3.12+
- PostgreSQL 16
- Docker & docker-compose (optional)

### Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/KKS071/is601-final-extended-calculator-suite
cd is601-final-extended-calculator-suite

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials and JWT secrets

# 5. Create the database
createdb fastapi_db
createdb fastapi_test_db

# 6. Start the app
uvicorn app.main:app --reload
```

Visit http://localhost:8000 in your browser.

### Docker Setup

```bash
# Build and start everything
docker-compose up --build

# Stop
docker-compose down
```

App: http://localhost:8000  
Swagger UI: http://localhost:8000/docs  
ReDoc: http://localhost:8000/redoc

---

## Test Instructions

```bash
# Run all unit + integration + e2e tests with coverage
pytest

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run E2E tests (requires running server at localhost:8000)
# First install Playwright: playwright install chromium
pytest tests/e2e/ --browser chromium

# View HTML coverage report
open htmlcov/index.html
```

Target: **100% coverage** across `app/`.

---

## API Reference

| Method | Endpoint                  | Auth | Description                        |
|--------|---------------------------|------|------------------------------------|
| POST   | `/auth/register`          | ✗    | Register a new user                |
| POST   | `/auth/login`             | ✗    | Login — returns JWT tokens         |
| POST   | `/auth/token`             | ✗    | OAuth2 form login (Swagger UI)     |
| GET    | `/users/me`               | ✓    | Get current user profile           |
| PUT    | `/users/me`               | ✓    | Update name / email / username     |
| PUT    | `/users/me/password`      | ✓    | Change password                    |
| POST   | `/calculations`           | ✓    | Add a new calculation              |
| GET    | `/calculations`           | ✓    | Browse all your calculations       |
| GET    | `/calculations/{id}`      | ✓    | Read one calculation               |
| PUT    | `/calculations/{id}`      | ✓    | Edit a calculation                 |
| DELETE | `/calculations/{id}`      | ✓    | Delete a calculation               |
| GET    | `/calculations/stats`     | ✓    | Aggregated stats                   |

Full interactive docs: http://localhost:8000/docs

---

## Docker Instructions

```bash
# Build image locally
docker build -t calcapp .

# Run container (requires external Postgres)
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e JWT_SECRET_KEY=your-secret \
  calcapp

# Pull from Docker Hub
docker pull kks59/is601-final-extended-calculator-suite:latest
```

---

## CI/CD Pipeline

The GitHub Actions pipeline runs on every push/PR to `main`:

1. **Test** — starts Postgres, runs `pytest --cov`, uploads coverage XML
2. **Trivy** — filesystem vulnerability scan (CRITICAL + HIGH)
3. **Docker** — builds and pushes to Docker Hub (on `main` only), then scans the pushed image

Required GitHub Secrets (`production` environment):
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `JWT_SECRET_KEY`
- `JWT_REFRESH_SECRET_KEY`

---

## Alembic Migrations (optional)

Tables are auto-created by SQLAlchemy on startup. If you want to use Alembic for migrations:

```bash
# Initialize
alembic init alembic

# Update alembic.ini with your DATABASE_URL, then:
alembic revision --autogenerate -m "initial"
alembic upgrade head

# Future migrations
alembic revision --autogenerate -m "add column"
alembic upgrade head
alembic downgrade -1
```

---

## Security Notes

- Passwords are hashed with bcrypt (12 rounds)
- JWT tokens are signed with HS256; access tokens expire in 30 minutes
- All calculation and user endpoints require a valid Bearer token
- Calculation ownership is enforced — users can only access their own records
- Input validation (empty inputs, division/modulo by zero, invalid types) is enforced at the Pydantic schema level

---

## Project Structure

```
.
├── app/
│   ├── auth/               # JWT utilities + FastAPI dependencies
│   ├── core/               # Settings (pydantic-settings)
│   ├── models/             # SQLAlchemy models (User, Calculation subtypes)
│   ├── schemas/            # Pydantic schemas
│   ├── database.py         # Engine + session factory
│   ├── database_init.py
│   ├── main.py             # All routes
│   └── operations.py       # Pure arithmetic functions
├── docs/
│   └── REFLECTION.md       # Project reflection and lessons learned
├── static/                 # CSS + JS
├── templates/              # Jinja2 HTML templates
├── tests/
│   ├── unit/               # Pure logic tests
│   ├── integration/        # API + DB tests
│   └── e2e/                # Playwright tests
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── requirements.txt
```
