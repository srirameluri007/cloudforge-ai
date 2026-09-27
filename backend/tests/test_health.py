"""Health, readiness, and Alembic migration round-trip tests."""

from __future__ import annotations

import os

from alembic.config import Config
from alembic import command


def test_health_ok(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"]


def test_ready_ok(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_health_has_security_headers(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Request-ID"]


def test_alembic_upgrade_downgrade_upgrade(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Run upgrade head -> downgrade base -> upgrade head against SQLite.

    CI runs this same test against PostgreSQL (see backend/README.md).
    """
    db_path = tmp_path / "alembic-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")

    # Verify a table from the migration exists and is usable.
    from sqlalchemy import create_engine, text

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        tables = {
            row[0]
            for row in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
        }
    assert "users" in tables
    assert "audit_events" in tables
    assert "credential_references" in tables
    engine.dispose()
    assert os.path.exists(db_path)
