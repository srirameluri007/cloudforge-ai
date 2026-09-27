"""Pytest fixtures.

Local runs use a file-based SQLite database (dependency override), because a
PostgreSQL server may not be available in this environment. CI and
docker-compose run the same suite against PostgreSQL -- see backend/README.md.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.database.session import get_db
from app.main import create_app

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("AI_PROVIDER", "demo")


@pytest.fixture()
def db_file(tmp_path) -> str:  # type: ignore[no-untyped-def]
    return str(tmp_path / f"test-{uuid.uuid4().hex}.db")


@pytest.fixture()
def session_factory(db_file: str):  # type: ignore[no-untyped-def]
    engine = create_engine(
        f"sqlite:///{db_file}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    engine.dispose()


@pytest.fixture()
def client(session_factory) -> Iterator[TestClient]:  # type: ignore[no-untyped-def]
    app = create_app()

    def override_get_db() -> Iterator[Session]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def db_session(session_factory) -> Iterator[Session]:  # type: ignore[no-untyped-def]
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def register(
    client: TestClient,
    email: str = "alice@example.com",
    password: str = "StrongPass123!",
    name: str = "Alice",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def make_project(client: TestClient, name: str = "Demo Project") -> dict:
    response = client.post(
        "/api/v1/projects",
        json={
            "name": name,
            "description": "Test project",
            "original_prompt": "Deploy a web app",
            "cloud_target": "azure",
            "environment": "development",
            "region": "eastus",
            "availability_requirement": "standard",
            "compliance_framework": "none",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def count_audit(
    db_session: Session, action: str, organization_id: str | None = None
) -> int:
    from app.models.audit import AuditEvent

    query = db_session.query(AuditEvent).filter(AuditEvent.action == action)
    if organization_id is not None:
        query = query.filter(AuditEvent.organization_id == organization_id)
    return query.count()
