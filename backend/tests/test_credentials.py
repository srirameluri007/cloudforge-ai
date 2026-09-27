"""Credential reference tests: metadata allowed, raw secrets rejected."""

from __future__ import annotations

from tests.conftest import count_audit, register

VALID = {
    "name": "Azure service principal",
    "provider": "azure",
    "auth_type": "managed-identity",
    "vault_reference": "vault://cloudforge/azure/spn-client-id",
    "description": "Client ID reference for the deployment identity.",
}


def test_credential_crud(client, db_session) -> None:  # type: ignore[no-untyped-def]
    body = register(client)
    org_id = body["organization"]["id"]

    created = client.post("/api/v1/credential-references", json=VALID)
    assert created.status_code == 201, created.text
    credential_id = created.json()["id"]
    assert count_audit(db_session, "credential.create", org_id) == 1

    listed = client.get("/api/v1/credential-references").json()
    assert any(c["id"] == credential_id for c in listed["items"])

    response = client.delete(f"/api/v1/credential-references/{credential_id}")
    assert response.status_code == 204
    assert count_audit(db_session, "credential.delete", org_id) == 1
    assert client.get("/api/v1/credential-references").json()["items"] == []


def test_credential_raw_secret_rejected(client, db_session) -> None:  # type: ignore[no-untyped-def]
    body = register(client)
    org_id = body["organization"]["id"]

    evil = dict(VALID)
    evil["vault_reference"] = "AKIAIOSFODNN7EXAMPLE"
    response = client.post("/api/v1/credential-references", json=evil)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "raw_secret_detected"

    evil2 = dict(VALID)
    evil2["description"] = "db password=SuperSecret123!"
    response2 = client.post("/api/v1/credential-references", json=evil2)
    assert response2.status_code == 422

    # The rejection itself is audited, and nothing was stored.
    assert count_audit(db_session, "credential.create.rejected", org_id) == 2
    assert client.get("/api/v1/credential-references").json()["items"] == []


def test_credential_tenant_isolation(client, session_factory) -> None:  # type: ignore[no-untyped-def]
    register(client, email="credowner@example.com")
    created = client.post("/api/v1/credential-references", json=VALID).json()

    from fastapi.testclient import TestClient

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
        register(other, email="credintruder@example.com", name="Intruder")
        assert other.get("/api/v1/credential-references").json()["items"] == []
        assert (
            other.delete(f"/api/v1/credential-references/{created['id']}").status_code
            == 404
        )
    app.dependency_overrides.clear()
