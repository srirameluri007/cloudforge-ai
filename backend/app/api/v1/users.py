"""User account routes: update own profile, delete own account."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current_user
from app.database.session import get_db
from app.models.membership import OrganizationMembership
from app.models.user import User
from app.schemas.auth import UserOut
from app.schemas.user import UserUpdateMe
from app.services import audit_service

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdateMe,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
) -> UserOut:
    user = db.query(User).filter(User.id == auth.user.id).first()
    assert user is not None
    user.name = payload.name
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
):
    user_id = auth.user.id
    organization_id = auth.organization.id
    audit_service.audit_event(
        db,
        action="user.delete",
        resource_type="user",
        resource_id=user_id,
        organization_id=organization_id,
        user_id=user_id,
        metadata={},
        request=request,
    )
    # Remove memberships first so the audit row keeps user_id=NULL via SET NULL.
    db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user_id
    ).delete(synchronize_session=False)
    db.flush()
    user = db.query(User).filter(User.id == user_id).first()
    if user is not None:
        db.delete(user)
    db.commit()
    response.delete_cookie(key="access_token", path="/")
