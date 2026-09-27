"""Project service: CRUD scoped to an organization."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(
    db: Session, *, organization_id: str, created_by_user_id: str, data: ProjectCreate
) -> Project:
    project = Project(
        organization_id=organization_id,
        created_by_user_id=created_by_user_id,
        name=data.name,
        description=data.description,
        original_prompt=data.original_prompt,
        cloud_target=data.cloud_target,
        environment=data.environment,
        region=data.region,
        availability_requirement=data.availability_requirement,
        compliance_framework=data.compliance_framework,
        status="draft",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(
    db: Session, *, organization_id: str, project_id: str
) -> Project | None:
    """Tenant-isolated lookup: returns None for cross-org access (callers map to 404)."""
    return (
        db.query(Project)
        .filter(Project.id == project_id, Project.organization_id == organization_id)
        .first()
    )


def list_projects(db: Session, *, organization_id: str) -> list[Project]:
    return (
        db.query(Project)
        .filter(Project.organization_id == organization_id)
        .order_by(Project.created_at.desc())
        .all()
    )


def update_project(db: Session, *, project: Project, data: ProjectUpdate) -> Project:
    changes = data.model_dump(exclude_unset=True)
    for field_name, value in changes.items():
        setattr(project, field_name, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, *, project: Project) -> None:
    db.delete(project)
    db.commit()
