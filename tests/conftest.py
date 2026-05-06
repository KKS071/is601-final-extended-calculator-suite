# File: tests/conftest.py
# Purpose: Shared fixtures — SQLite in-memory (StaticPool) for fast, isolated tests.
import uuid
import pytest
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.calculation import Calculation  # noqa: F401

faker = Faker()

# Single shared in-memory SQLite DB across all connections
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session(setup_test_db):
    """Each test gets a fresh session. Data is committed so cross-query reads work."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(db_session) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        password=User.hash_password("TestPass123!"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def auth_headers(client, test_user):
    resp = client.post("/auth/login", json={
        "username": test_user.username,
        "password": "TestPass123!",
    })
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
