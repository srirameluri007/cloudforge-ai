"""Asset listing / retrieval / download tests."""

from __future__ import annotations

from tests.conftest import make_project, register


def _generate(client, project_id: str) -> dict:  # type: ignore[no-untyped-def]
    response = client.post(f"/api/v1/projects/{project_id}/generate", json={})
    assert response.status_code == 200, response.text
    return response.json()


def test_assets_list_get_download(client) -> None:  # type: ignore[no-untyped-def]
    register(client)
    project = make_project(client)
    generation = _generate(client, project["id"])

    listed = client.get(f"/api/v1/generations/{generation['id']}/assets").json()
    items = listed["items"]
    assert len(items) >= 16
    # List view must NOT include content.
    assert all("content" not in item for item in items)
    first = items[0]
    assert {
        "id",
        "asset_type",
        "file_name",
        "language",
        "content_hash",
        "created_at",
    } <= set(first)

    fetched = client.get(f"/api/v1/assets/{first['id']}").json()
    assert fetched["content"].strip()
    assert fetched["content_hash"] == first["content_hash"]

    download = client.get(f"/api/v1/assets/{first['id']}/download")
    assert download.status_code == 200
    assert "attachment" in download.headers["content-disposition"]
    assert download.text == fetched["content"]


def test_asset_not_found(client) -> None:  # type: ignore[no-untyped-def]
    register(client)
    assert client.get("/api/v1/assets/does-not-exist").status_code == 404
