"""Auth routes: register / login / logout / me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current_user, get_request_id_dep, settings
from app.core.security import create_access_token, validate_password_policy
from app.database.session import get_db
from app.models.organization import Organization
from app.schemas.auth import (
    AuthMeResponse,
    LoginRequest,
    OrganizationOut,
    RegisterRequest,
    UserOut,
)
from app.schemas.common import error_envelope
from app.services import audit_service
from app.services.auth_service import (
    EmailAlreadyRegistered,
    authenticate_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "access_token"


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _issue_token(user_id: str, organization_id: str) -> str:
    return create_access_token(
        user_id=user_id,
        organization_id=organization_id,
        secret=settings.JWT_SECRET,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id_dep),
) -> dict[str, object]:
    policy_errors = validate_password_policy(payload.password)
    if policy_errors:
        raise HTTPException(
            status_code=422,
            detail=error_envelope(
                "weak_password",
                "Password does not meet the security policy.",
                request_id,
                {"password": policy_errors},
            ),
        )

    try:
        user, organization = register_user(
            db, name=payload.name, email=str(payload.email), password=payload.password
        )
    except EmailAlreadyRegistered as exc:
        raise HTTPException(
            status_code=409,
            detail=error_envelope("email_taken", str(exc), request_id),
        )

    audit_service.audit_event(
        db,
        action="user.register",
        resource_type="user",
        resource_id=user.id,
        organization_id=organization.id,
        user_id=user.id,
        metadata={"email_domain": str(payload.email).split("@")[-1]},
        request=request,
    )
    _set_auth_cookie(response, _issue_token(user.id, organization.id))
    return {
        "user": UserOut.model_validate(user).model_dump(),
        "organization": OrganizationOut.model_validate(organization).model_dump(),
    }


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    request_id: str = Depends(get_request_id_dep),
) -> dict[str, object]:
    user = authenticate_user(db, email=str(payload.email), password=payload.password)
    if user is None:
        audit_service.audit_event(
            db,
            action="auth.login.failure",
            resource_type="user",
            resource_id=None,
            organization_id=None,
            user_id=None,
            metadata={},
            request=request,
        )
        raise HTTPException(
            status_code=401,
            detail=error_envelope(
                "invalid_credentials", "Invalid email or password.", request_id
            ),
        )

    organization_id, role = audit_service.get_user_org(db, user)
    organization = (
        db.query(Organization).filter(Organization.id == organization_id).first()
    )
    audit_service.audit_event(
        db,
        action="auth.login.success",
        resource_type="user",
        resource_id=user.id,
        organization_id=organization_id,
        user_id=user.id,
        metadata={},
        request=request,
    )
    _set_auth_cookie(response, _issue_token(user.id, organization_id))
    return {
        "user": UserOut.model_validate(user).model_dump(),
        "organization": OrganizationOut.model_validate(organization).model_dump(),
        "role": role,
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
) -> dict[str, object]:
    audit_service.audit_event(
        db,
        action="auth.logout",
        resource_type="user",
        resource_id=auth.user.id,
        organization_id=auth.organization.id,
        user_id=auth.user.id,
        metadata={},
        request=request,
    )
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me", response_model=AuthMeResponse)
def me(auth: AuthContext = Depends(get_current_user)) -> AuthMeResponse:
    return AuthMeResponse(
        user=UserOut.model_validate(auth.user),
        organization=OrganizationOut.model_validate(auth.organization),
        role=auth.role,
    )
