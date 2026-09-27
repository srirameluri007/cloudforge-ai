"""Credential reference schemas (metadata only -- never raw secrets)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CredentialReferenceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    provider: str = Field(min_length=1, max_length=64)
    auth_type: str = Field(min_length=1, max_length=64)
    vault_reference: str = Field(min_length=1, max_length=512)
    description: str | None = Field(default=None, max_length=2000)


class CredentialReferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    name: str
    provider: str
    auth_type: str
    vault_reference: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class CredentialReferenceList(BaseModel):
    items: list[CredentialReferenceOut]
