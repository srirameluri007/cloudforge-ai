"""Auth service: registration and credential verification."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User


class AuthError(Exception):
    pass


class EmailAlreadyRegistered(AuthError):
    pass


def register_user(
    db: Session, *, name: str, email: str, password: str
) -> tuple[User, Organization]:
    normalized_email = email.strip().lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing is not None:
        raise EmailAlreadyRegistered("An account with this email already exists.")

    user = User(
        name=name.strip(), email=normalized_email, password_hash=hash_password(password)
    )
    db.add(user)
    db.flush()

    organization = Organization(name=f"{user.name}'s Organization")
    db.add(organization)
    db.flush()

    membership = OrganizationMembership(
        organization_id=organization.id, user_id=user.id, role="admin"
    )
    db.add(membership)
    db.commit()
    db.refresh(user)
    db.refresh(organization)
    return user, organization


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    """Return the user on success; None for unknown user OR bad password.

    Callers must use a generic error message so as not to reveal which failed.
    """
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
