"""ZIP export tests, including traversal safety."""

from __future__ import annotations

import io
import json
import zipfile

from tests.conftest import count_audit, make_project, register


def _generate(client, project_id: str) -> dict:  # type: ignore[no-untyped-def]
    response = client.post(f"/api/v1/projects/{project_id}/generate", json={})
    assert response.status_code == 200, response.text
    return response.json()


def test_export_zip_layout(client, db_session) -> None:  # type: ignore[no-untyped-def]
    body = register(client)
    org_id = body["organization"]["id"]
    project = make_project(client, name="Export Me")
    generation = _generate(client, project["id"])

    response = client.get(f"/api/v1/generations/{generation['id']}/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers["content-disposition"]
    assert "cloudforge-export_me-" in response.headers["content-disposition"].lower()

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    names = zf.namelist()
    assert "generated-project/generation_metadata.json" in names
    assert "generated-project/README.md" in names
    for expected_dir in (
        "generated-project/terraform/",
        "generated-project/bicep/",
        "generated-project/arm/",
        "generated-project/cloudformation/",
        "generated-project/kubernetes/",
        "generated-project/helm/",
        "generated-project/pipelines/github-actions/",
        "generated-project/pipelines/azure-devops/",
        "generated-project/pipelines/jenkins/",
        "generated-project/pipelines/gitlab-ci/",
        "generated-project/docs/",
        "generated-project/security/",
    ):
        assert any(n.startswith(expected_dir) for n in names), expected_dir
    # No entry escapes the root directory.
    assert all(n.startswith("generated-project/") and ".." not in n for n in names)

    metadata = json.loads(zf.read("generated-project/generation_metadata.json"))
    assert metadata["provider"] == "demo"
    assert metadata["demo"] is True
    assert metadata["assumptions"]
    assert metadata["limitations"]
    assert metadata["project"]["name"] == "Export Me"

    assert count_audit(db_session, "project.export", org_id) == 1


def test_export_sanitizes_traversal_filenames() -> None:
    from app.services.export_service import (
        ExportAsset,
        build_metadata,
        build_zip,
        sanitize_filename,
    )

    assert sanitize_filename("../../evil.txt", "terraform") is None
    assert sanitize_filename("..\\evil.tf", "terraform") is None
    assert sanitize_filename("/abs/path.tf", "terraform") is None
    assert sanitize_filename("main.tf", "terraform") == "main.tf"
    assert sanitize_filename("main.tf", "arm") is None  # wrong extension for type
    assert sanitize_filename("Jenkinsfile", "jenkins") == "Jenkinsfile"

    assets = [
        ExportAsset(asset_type="terraform", file_name="../../evil.tf", content="x"),
        ExportAsset(asset_type="terraform", file_name="main.tf", content="content"),
    ]
    result = build_zip(
        assets,
        metadata=build_metadata(
            provider="demo",
            model="demo",
            generation_id="g1",
            project={},
            started_at=None,
            completed_at=None,
            assumptions=[],
        ),
    )
    assert result.skipped == ["terraform:../../evil.tf"]
    zf = zipfile.ZipFile(io.BytesIO(result.data))
    names = zf.namelist()
    assert "generated-project/terraform/main.tf" in names
    assert all(".." not in n for n in names)
