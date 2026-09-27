"""Project CRUD routes (tenant-isolated: cross-org access returns 404)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current_user, get_request_id_dep
from app.core.config import get_settings
from app.database.session import get_db
from app.models.project import Project
from app.schemas.common import error_envelope
from app.schemas.generation import GenerateRequest, GenerationOut
from app.schemas.project import ProjectCreate, ProjectList, ProjectOut, ProjectUpdate
from app.services import audit_service, project_service
from app.services.generation_service import run_generation

router = APIRouter(prefix="/projects", tags=["projects"])
settings = get_settings()


def _get_project_or_404(
    db: Session, auth: AuthContext, project_id: str, request_id: str
) -> Project:
    project = project_service.get_project(
        db, organization_id=auth.organization.id, project_id=project_id
    )
    if project is None:
        raise HTTPException(
            status_code=404,
            detail=error_envelope("not_found", "Project not found.", request_id),
        )
    return project


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
) -> ProjectOut:
    project = project_service.create_project(
        db,
        organization_id=auth.organization.id,
        created_by_user_id=auth.user.id,
        data=payload,
    )
    audit_service.audit_event(
        db,
        action="project.create",
        resource_type="project",
        resource_id=project.id,
        organization_id=auth.organization.id,
        user_id=auth.user.id,
        metadata={"name": project.name, "cloud_target": project.cloud_target},
        request=request,
    )
    return ProjectOut.model_validate(project)


@router.get("", response_model=ProjectList)
def list_projects(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
) -> ProjectList:
    projects = project_service.list_projects(db, organization_id=auth.organization.id)
    return ProjectList(items=[ProjectOut.model_validate(p) for p in projects])


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
) -> ProjectOut:
    project = _get_project_or_404(db, auth, project_id, request_id)
    return ProjectOut.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    payload: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
) -> ProjectOut:
    project = _get_project_or_404(db, auth, project_id, request_id)
    project = project_service.update_project(db, project=project, data=payload)
    audit_service.audit_event(
        db,
        action="project.update",
        resource_type="project",
        resource_id=project.id,
        organization_id=auth.organization.id,
        user_id=auth.user.id,
        metadata={},
        request=request,
    )
    return ProjectOut.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    request: Request,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
):
    project = _get_project_or_404(db, auth, project_id, request_id)
    project_service.delete_project(db, project=project)
    audit_service.audit_event(
        db,
        action="project.delete",
        resource_type="project",
        resource_id=project_id,
        organization_id=auth.organization.id,
        user_id=auth.user.id,
        metadata={},
        request=request,
    )


@router.post("/{project_id}/generate")
def generate_project(
    project_id: str,
    payload: GenerateRequest,
    request: Request,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
) -> dict[str, object]:
    project = _get_project_or_404(db, auth, project_id, request_id)
    audit_service.audit_event(
        db,
        action="generation.start",
        resource_type="project",
        resource_id=project.id,
        organization_id=auth.organization.id,
        user_id=auth.user.id,
        metadata={},
        request=request,
    )
    generation = run_generation(
        db,
        project=project,
        prompt_override=payload.prompt,
        settings=settings,
    )
    if generation.status == "failed":
        audit_service.audit_event(
            db,
            action="generation.failed",
            resource_type="generation",
            resource_id=generation.id,
            organization_id=auth.organization.id,
            user_id=auth.user.id,
            metadata={},
            request=request,
        )
    else:
        audit_service.audit_event(
            db,
            action="generation.success",
            resource_type="generation",
            resource_id=generation.id,
            organization_id=auth.organization.id,
            user_id=auth.user.id,
            metadata={"provider": generation.provider},
            request=request,
        )
    return GenerationOut.model_validate(generation).model_dump()
