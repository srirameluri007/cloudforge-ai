"""Audit event schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    organization_id: str
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    metadata: dict[str, Any] | None = Field(default=None, alias="event_metadata")
    source_ip: str | None
    created_at: datetime


class AuditEventList(BaseModel):
    items: list[AuditEventOut]
