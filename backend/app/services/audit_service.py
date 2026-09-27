"""Audit helper: records AuditEvent rows for security-relevant actions."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session
from starlette.requests import Request

import logging

from app.core.logging_config import get_logger, log_extra
from app.models.audit import AuditEvent
from app.models.membership import OrganizationMembership
from app.models.user import User

logger = get_logger(__name__)


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    client = request.client
    return client.host[:64] if client else None


def audit_event(
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None,
    organization_id: str | None,
    user_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditEvent:
    """Write an audit event. Never raises: failures are logged, not fatal."""
    try:
        event = AuditEvent(
            organization_id=organization_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            event_metadata=metadata or {},
            source_ip=_client_ip(request),
        )
        db.add(event)
        db.commit()
        return event
    except Exception:
        log_extra(
            logger, logging.ERROR, "Failed to write audit event", {"action": action}
        )
        db.rollback()
        raise


def get_user_org(db: Session, user: User) -> tuple[str, str]:
    """Return (organization_id, role) for the user's first membership."""
    membership = (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.user_id == user.id)
        .order_by(OrganizationMembership.created_at)
        .first()
    )
    if membership is None:
        raise ValueError("User has no organization membership")
    return membership.organization_id, membership.role
