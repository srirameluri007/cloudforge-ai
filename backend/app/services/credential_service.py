"""Credential reference service (metadata only -- never raw secrets)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import contains_raw_secret
from app.models.credential import CredentialReference


class RawSecretDetected(Exception):
    def __init__(self, pattern_name: str | None) -> None:
        super().__init__("Input appears to contain a raw secret value.")
        self.pattern_name = pattern_name


def create_credential_reference(
    db: Session,
    *,
    organization_id: str,
    name: str,
    provider: str,
    auth_type: str,
    vault_reference: str,
    description: str | None,
) -> CredentialReference:
    detected, pattern_name = contains_raw_secret(
        {
            "name": name,
            "provider": provider,
            "auth_type": auth_type,
            "vault_reference": vault_reference,
            "description": description,
        }
    )
    if detected:
        raise RawSecretDetected(pattern_name)
    credential = CredentialReference(
        organization_id=organization_id,
        name=name,
        provider=provider,
        auth_type=auth_type,
        vault_reference=vault_reference,
        description=description,
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential
