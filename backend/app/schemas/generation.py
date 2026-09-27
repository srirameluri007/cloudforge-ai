"""Generation schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    prompt: str | None = Field(default=None, max_length=20000)


class GenerationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    provider: str
    model: str
    status: str
    structured_output: dict[str, Any] | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class GenerationList(BaseModel):
    items: list[GenerationOut]
