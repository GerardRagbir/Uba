"""Test setup: every test gets a fresh, empty in-memory database."""

import os

os.environ["UBA_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["UBA_SMTP_PORT"] = "1"  # nothing listens here, so no email is really sent

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    with TestClient(app) as test_client:  # runs startup, which creates tables and demo data
        yield test_client


def login(client: TestClient, username: str, password: str) -> None:
    client.cookies.clear()
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
