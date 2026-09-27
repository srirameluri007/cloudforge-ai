"""Shared API dependencies: cookie-JWT auth, org admin guard, request id."""

from __future__ import annotations

import jwt
from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging_config import get_request_id
from app.core.security import verify_access_token
from app.database.session import get_db
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.common import error_envelope

settings = get_settings()


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=error_envelope("unauthorized", detail, get_request_id() or ""),
    )


class AuthContext:
    def __init__(self, user: User, organization: Organization, role: str) -> None:
        self.user = user
        self.organization = organization
        self.role = role


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None),
) -> AuthContext:
    if not access_token:
        raise _unauthorized()
    try:
        claims = verify_access_token(access_token, settings.JWT_SECRET)
    except jwt.PyJWTError:
        raise _unauthorized("Invalid or expired token")

    user_id = claims.get("sub")
    org_id = claims.get("org")
    if not user_id or not org_id:
        raise _unauthorized("Invalid token claims")

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        raise _unauthorized()
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if organization is None:
        raise _unauthorized()
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == organization.id,
        )
        .first()
    )
    if membership is None:
        raise _unauthorized()
    return AuthContext(user=user, organization=organization, role=membership.role)


def require_org_admin(auth: AuthContext = Depends(get_current_user)) -> AuthContext:
    if auth.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_envelope(
                "forbidden",
                "Organization admin access required.",
                get_request_id() or "",
            ),
        )
    return auth


def get_request_id_dep() -> str:
    return get_request_id() or ""
