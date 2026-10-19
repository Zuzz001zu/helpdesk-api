import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import app

# CI runs the suite against PostgreSQL; locally SQLite in memory is enough.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite:///:memory:")
API_KEY = "test-key"

if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
else:
    engine = create_engine(TEST_DATABASE_URL)

TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db():
    Base.metadata.create_all(engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=API_KEY)
    with TestClient(app, headers={"X-API-Key": API_KEY}) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def make_ticket(client):
    def _make(**overrides):
        payload = {
            "title": "VPN does not connect",
            "description": "Error 809 since this morning",
            "requester_email": "anna.muller@example.com",
            "category": "network",
            "priority": "high",
        }
        payload.update(overrides)
        response = client.post("/tickets", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make
