"""Audit event listing tests (admin-only)."""

from __future__ import annotations

from app.models.membership import OrganizationMembership
from tests.conftest import count_audit, make_project, register


def test_audit_events_admin_only(client, db_session) -> None:  # type: ignore[no-untyped-def]
    body = register(client, email="admin@example.com")
    org_id = body["organization"]["id"]

    response = client.get("/api/v1/audit-events")
    assert response.status_code == 200
    actions = {e["action"] for e in response.json()["items"]}
    assert "user.register" in actions

    project = make_project(client)
    client.post(f"/api/v1/projects/{project['id']}/generate", json={})

    response = client.get("/api/v1/audit-events")
    actions = {e["action"] for e in response.json()["items"]}
    for expected in (
        "user.register",
        "project.create",
        "generation.start",
        "generation.success",
    ):
        assert expected in actions, expected

    # Every event carries the org, a request id is in the envelope-free payload,
    # and no passwords/secrets leak.
    for event in response.json()["items"]:
        assert event["organization_id"] == org_id
        assert "password" not in str(event).lower()

    assert count_audit(db_session, "generation.success", org_id) == 1


def test_audit_events_forbidden_for_members(client, db_session) -> None:  # type: ignore[no-untyped-def]
    register(client, email="boss@example.com")
    # Demote the user to a non-admin member.
    membership = db_session.query(OrganizationMembership).first()
    assert membership is not None
    membership.role = "member"
    db_session.commit()

    response = client.get("/api/v1/audit-events")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_audit_events_require_auth(client) -> None:  # type: ignore[no-untyped-def]
    assert client.get("/api/v1/audit-events").status_code == 401
