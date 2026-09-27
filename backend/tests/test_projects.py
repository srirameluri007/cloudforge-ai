"""Project CRUD + tenant isolation tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import count_audit, make_project, register


def test_project_crud(client, db_session) -> None:  # type: ignore[no-untyped-def]
    body = register(client)
    org_id = body["organization"]["id"]

    created = make_project(client, name="CRUD Project")
    project_id = created["id"]
    assert created["organization_id"] == org_id
    assert count_audit(db_session, "project.create", org_id) == 1

    listed = client.get("/api/v1/projects").json()
    assert listed["items"] and any(p["id"] == project_id for p in listed["items"])

    fetched = client.get(f"/api/v1/projects/{project_id}").json()
    assert fetched["name"] == "CRUD Project"

    updated = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Renamed", "region": "westeurope"},
    ).json()
    assert updated["name"] == "Renamed"
    assert updated["region"] == "westeurope"
    assert count_audit(db_session, "project.update", org_id) == 1

    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/projects/{project_id}").status_code == 404
    assert count_audit(db_session, "project.delete", org_id) == 1


def test_project_tenant_isolation(client, session_factory) -> None:  # type: ignore[no-untyped-def]
    register(client, email="owner@example.com")
    project = make_project(client, name="Secret Project")
    project_id = project["id"]

    # A user from a different organization shares the same DB but must see nothing.
    from app.database.session import get_db
    from app.main import create_app

    app = create_app()

    def override_get_db():  # type: ignore[no-untyped-def]
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as other:
        register(other, email="intruder@example.com", name="Intruder")

        assert other.get("/api/v1/projects").json()["items"] == []
        assert other.get(f"/api/v1/projects/{project_id}").status_code == 404
        assert (
            other.patch(
                f"/api/v1/projects/{project_id}", json={"name": "x"}
            ).status_code
            == 404
        )
        assert other.delete(f"/api/v1/projects/{project_id}").status_code == 404
        assert (
            other.post(f"/api/v1/projects/{project_id}/generate", json={}).status_code
            == 404
        )
    app.dependency_overrides.clear()


def test_project_create_validation(client) -> None:  # type: ignore[no-untyped-def]
    register(client)
    response = client.post("/api/v1/projects", json={"name": "", "cloud_target": "gcp"})
    assert response.status_code == 422
