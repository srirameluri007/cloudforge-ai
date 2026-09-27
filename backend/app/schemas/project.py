"""Project schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CloudTarget = Literal["azure", "aws", "multi-cloud"]
Environment = Literal["development", "test", "production"]
AvailabilityRequirement = Literal["standard", "high-availability", "multi-region"]
ComplianceFramework = Literal["none", "cis", "nist", "soc2", "pci-dss", "iso27001"]
ProjectStatus = Literal["draft", "generating", "ready", "failed"]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    original_prompt: str | None = Field(default=None, max_length=20000)
    cloud_target: CloudTarget = "azure"
    environment: Environment = "development"
    region: str = Field(default="eastus", min_length=1, max_length=64)
    availability_requirement: AvailabilityRequirement = "standard"
    compliance_framework: ComplianceFramework = "none"


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    original_prompt: str | None = Field(default=None, max_length=20000)
    cloud_target: CloudTarget | None = None
    environment: Environment | None = None
    region: str | None = Field(default=None, min_length=1, max_length=64)
    availability_requirement: AvailabilityRequirement | None = None
    compliance_framework: ComplianceFramework | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    created_by_user_id: str | None
    name: str
    description: str | None
    original_prompt: str | None
    cloud_target: str
    environment: str
    region: str
    availability_requirement: str
    compliance_framework: str
    status: str
    created_at: datetime
    updated_at: datetime


class ProjectList(BaseModel):
    items: list[ProjectOut]
