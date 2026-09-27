"""Generation routes: list, get, retry, assets, export."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current_user, get_request_id_dep
from app.core.config import get_settings
from app.database.session import get_db
from app.models.asset import GeneratedAsset
from app.models.generation import Generation
from app.models.project import Project
from app.schemas.asset import AssetList, AssetSummaryOut
from app.schemas.common import error_envelope
from app.schemas.generation import GenerateRequest, GenerationList, GenerationOut
from app.services import audit_service
from app.services.export_service import (
    ExportAsset,
    build_metadata,
    build_zip,
    sanitize_archive_filename,
)
from app.services.generation_service import run_generation
from app.services.project_service import get_project as get_project_for_org

router = APIRouter(tags=["generations"])
settings = get_settings()


def _not_found(request_id: str, message: str = "Not found.") -> HTTPException:
    return HTTPException(
        status_code=404, detail=error_envelope("not_found", message, request_id)
    )


def _get_generation_or_404(
    db: Session, auth: AuthContext, generation_id: str, request_id: str
) -> tuple[Generation, Project]:
    """Tenant-isolated generation lookup (cross-org -> 404)."""
    row = (
        db.query(Generation, Project)
        .join(Project, Generation.project_id == Project.id)
        .filter(
            Generation.id == generation_id,
            Project.organization_id == auth.organization.id,
        )
        .first()
    )
    if row is None:
        raise _not_found(request_id, "Generation not found.")
    generation, project = row
    return generation, project


@router.get("/projects/{project_id}/generations", response_model=GenerationList)
def list_generations(
    project_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
) -> GenerationList:
    project = get_project_for_org(
        db, organization_id=auth.organization.id, project_id=project_id
    )
    if project is None:
        raise _not_found(request_id, "Project not found.")
    generations = (
        db.query(Generation)
        .filter(Generation.project_id == project.id)
        .order_by(Generation.created_at.desc())
        .all()
    )
    return GenerationList(items=[GenerationOut.model_validate(g) for g in generations])


@router.get("/generations/{generation_id}", response_model=GenerationOut)
def get_generation(
    generation_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
) -> GenerationOut:
    generation, _ = _get_generation_or_404(db, auth, generation_id, request_id)
    return GenerationOut.model_validate(generation)


@router.post("/generations/{generation_id}/retry", status_code=status.HTTP_201_CREATED)
def retry_generation(
    generation_id: str,
    payload: GenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
) -> dict[str, object]:
    _, project = _get_generation_or_404(db, auth, generation_id, request_id)
    audit_service.audit_event(
        db,
        action="generation.start",
        resource_type="project",
        resource_id=project.id,
        organization_id=auth.organization.id,
        user_id=auth.user.id,
        metadata={"retry_of": generation_id},
        request=request,
    )
    generation = run_generation(
        db, project=project, prompt_override=payload.prompt, settings=settings
    )
    audit_service.audit_event(
        db,
        action="generation.success"
        if generation.status == "succeeded"
        else "generation.failed",
        resource_type="generation",
        resource_id=generation.id,
        organization_id=auth.organization.id,
        user_id=auth.user.id,
        metadata={"retry_of": generation_id},
        request=request,
    )
    return GenerationOut.model_validate(generation).model_dump()


@router.get("/generations/{generation_id}/assets", response_model=AssetList)
def list_generation_assets(
    generation_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
) -> AssetList:
    generation, _ = _get_generation_or_404(db, auth, generation_id, request_id)
    assets = (
        db.query(GeneratedAsset)
        .filter(GeneratedAsset.generation_id == generation.id)
        .order_by(GeneratedAsset.asset_type, GeneratedAsset.file_name)
        .all()
    )
    return AssetList(items=[AssetSummaryOut.model_validate(a) for a in assets])


@router.get("/generations/{generation_id}/export")
def export_generation(
    generation_id: str,
    request: Request,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
) -> Response:
    generation, project = _get_generation_or_404(db, auth, generation_id, request_id)
    assets = (
        db.query(GeneratedAsset)
        .filter(GeneratedAsset.generation_id == generation.id)
        .order_by(GeneratedAsset.asset_type, GeneratedAsset.file_name)
        .all()
    )
    export_assets = [
        ExportAsset(asset_type=a.asset_type, file_name=a.file_name, content=a.content)
        for a in assets
    ]
    structured = generation.structured_output or {}
    metadata = build_metadata(
        provider=generation.provider,
        model=generation.model,
        generation_id=generation.id,
        project={
            "id": project.id,
            "name": project.name,
            "cloud_target": project.cloud_target,
            "environment": project.environment,
            "region": project.region,
            "availability_requirement": project.availability_requirement,
            "compliance_framework": project.compliance_framework,
        },
        started_at=generation.started_at,
        completed_at=generation.completed_at,
        assumptions=list(structured.get("assumptions", [])),
    )
    result = build_zip(export_assets, metadata=metadata)

    audit_service.audit_event(
        db,
        action="project.export",
        resource_type="generation",
        resource_id=generation.id,
        organization_id=auth.organization.id,
        user_id=auth.user.id,
        metadata={"included": len(result.included), "skipped": len(result.skipped)},
        request=request,
    )

    filename = (
        f"cloudforge-{sanitize_archive_filename(project.name)}"
        f"-{sanitize_archive_filename(generation.id[:8])}.zip"
    )
    return Response(
        content=result.data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
