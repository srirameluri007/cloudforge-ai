"""Asset routes: get single asset (with content) and download."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current_user, get_request_id_dep
from app.database.session import get_db
from app.models.asset import GeneratedAsset
from app.models.generation import Generation
from app.models.project import Project
from app.schemas.asset import AssetOut
from app.schemas.common import error_envelope
from app.services import audit_service
from app.services.export_service import sanitize_archive_filename, sanitize_filename

router = APIRouter(prefix="/assets", tags=["assets"])

_CONTENT_TYPES = {
    ".tf": "text/plain",
    ".bicep": "text/plain",
    ".json": "application/json",
    ".yaml": "text/yaml",
    ".yml": "text/yaml",
    ".groovy": "text/plain",
    ".md": "text/markdown",
}


def _get_asset_or_404(
    db: Session, auth: AuthContext, asset_id: str, request_id: str
) -> GeneratedAsset:
    row = (
        db.query(GeneratedAsset, Generation, Project)
        .join(Generation, GeneratedAsset.generation_id == Generation.id)
        .join(Project, Generation.project_id == Project.id)
        .filter(
            GeneratedAsset.id == asset_id,
            Project.organization_id == auth.organization.id,
        )
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=error_envelope("not_found", "Asset not found.", request_id),
        )
    asset, _, _ = row
    return asset


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
) -> AssetOut:
    asset = _get_asset_or_404(db, auth, asset_id, request_id)
    return AssetOut.model_validate(asset)


@router.get("/{asset_id}/download")
def download_asset(
    asset_id: str,
    request: Request,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
) -> Response:
    asset = _get_asset_or_404(db, auth, asset_id, request_id)
    safe_name = sanitize_filename(asset.file_name, asset.asset_type) or "asset.txt"

    audit_service.audit_event(
        db,
        action="asset.download",
        resource_type="asset",
        resource_id=asset.id,
        organization_id=auth.organization.id,
        user_id=auth.user.id,
        metadata={"file_name": safe_name},
        request=request,
    )

    _, ext = os.path.splitext(safe_name)
    content_type = _CONTENT_TYPES.get(ext.lower(), "application/octet-stream")
    return Response(
        content=asset.content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{sanitize_archive_filename(safe_name)}"'
        },
    )
