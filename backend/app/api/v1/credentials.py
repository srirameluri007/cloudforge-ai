"""Credential reference routes (metadata only -- never raw secrets)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current_user, get_request_id_dep
from app.database.session import get_db
from app.models.credential import CredentialReference
from app.schemas.common import error_envelope
from app.schemas.credential import (
    CredentialReferenceCreate,
    CredentialReferenceList,
    CredentialReferenceOut,
)
from app.services import audit_service
from app.services.credential_service import (
    RawSecretDetected,
    create_credential_reference,
)

router = APIRouter(prefix="/credential-references", tags=["credentials"])


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=CredentialReferenceOut
)
def create_credential(
    payload: CredentialReferenceCreate,
    request: Request,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
) -> CredentialReferenceOut:
    try:
        credential = create_credential_reference(
            db,
            organization_id=auth.organization.id,
            name=payload.name,
            provider=payload.provider,
            auth_type=payload.auth_type,
            vault_reference=payload.vault_reference,
            description=payload.description,
        )
    except RawSecretDetected:
        audit_service.audit_event(
            db,
            action="credential.create.rejected",
            resource_type="credential_reference",
            resource_id=None,
            organization_id=auth.organization.id,
            user_id=auth.user.id,
            metadata={"name": payload.name, "reason": "raw_secret_detected"},
            request=request,
        )
        raise HTTPException(
            status_code=422,
            detail=error_envelope(
                "raw_secret_detected",
                "Input appears to contain a raw secret. Only vault references are allowed.",
                request_id,
            ),
        )
    audit_service.audit_event(
        db,
        action="credential.create",
        resource_type="credential_reference",
        resource_id=credential.id,
        organization_id=auth.organization.id,
        user_id=auth.user.id,
        metadata={"name": credential.name, "provider": credential.provider},
        request=request,
    )
    return CredentialReferenceOut.model_validate(credential)


@router.get("", response_model=CredentialReferenceList)
def list_credentials(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
) -> CredentialReferenceList:
    credentials = (
        db.query(CredentialReference)
        .filter(CredentialReference.organization_id == auth.organization.id)
        .order_by(CredentialReference.created_at.desc())
        .all()
    )
    return CredentialReferenceList(
        items=[CredentialReferenceOut.model_validate(c) for c in credentials]
    )


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credential(
    credential_id: str,
    request: Request,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_current_user),
    request_id: str = Depends(get_request_id_dep),
):
    credential = (
        db.query(CredentialReference)
        .filter(
            CredentialReference.id == credential_id,
            CredentialReference.organization_id == auth.organization.id,
        )
        .first()
    )
    if credential is None:
        raise HTTPException(
            status_code=404,
            detail=error_envelope(
                "not_found", "Credential reference not found.", request_id
            ),
        )
    db.delete(credential)
    db.commit()
    audit_service.audit_event(
        db,
        action="credential.delete",
        resource_type="credential_reference",
        resource_id=credential_id,
        organization_id=auth.organization.id,
        user_id=auth.user.id,
        metadata={},
        request=request,
    )
