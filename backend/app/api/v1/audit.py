"""Audit event listing (organization admins only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_org_admin
from app.database.session import get_db
from app.models.audit import AuditEvent
from app.schemas.audit import AuditEventList, AuditEventOut

router = APIRouter(tags=["audit"])


@router.get("/audit-events", response_model=AuditEventList)
def list_audit_events(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_org_admin),
) -> AuditEventList:
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.organization_id == auth.organization.id)
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return AuditEventList(items=[AuditEventOut.model_validate(e) for e in events])
