"""Pydantic contract for structured generation output + the AI system prompt.

Every provider must produce a StructuredGenerationResult that validates here
before anything is persisted. Invalid output is rejected with a sanitized
error and the caller gets a retry option.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Severity = Literal["critical", "high", "medium", "low", "informational"]

ASSET_TYPES: list[str] = [
    "terraform",
    "bicep",
    "arm",
    "cloudformation",
    "kubernetes",
    "helm",
    "github-actions",
    "azure-devops",
    "jenkins",
    "gitlab-ci",
    "architecture",
    "deployment",
    "security",
    "zero-trust",
    "cost",
    "readme",
]


class ArchitectureComponent(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    purpose: str = Field(min_length=1, max_length=2000)


class Architecture(BaseModel):
    overview: str = Field(min_length=1, max_length=10000)
    components: list[ArchitectureComponent] = Field(min_length=1)
    traffic_flow: list[str] = Field(min_length=1)


class GeneratedFile(BaseModel):
    asset_type: str = Field(min_length=1, max_length=64)
    file_name: str = Field(min_length=1, max_length=255)
    language: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=200000)

    @field_validator("asset_type")
    @classmethod
    def asset_type_known(cls, value: str) -> str:
        if value not in ASSET_TYPES:
            raise ValueError(
                f"Unknown asset_type '{value}'. Must be one of: {ASSET_TYPES}"
            )
        return value


class SecurityFinding(BaseModel):
    severity: Severity
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=5000)
    recommendation: str = Field(min_length=1, max_length=5000)


class ZeroTrust(BaseModel):
    identity_score: int = Field(ge=0, le=100)
    network_score: int = Field(ge=0, le=100)
    data_score: int = Field(ge=0, le=100)
    workload_score: int = Field(ge=0, le=100)
    overall_score: int = Field(ge=0, le=100)
    recommendations: list[str] = Field(min_length=1)


class CostGuidance(BaseModel):
    disclaimer: str = Field(min_length=1, max_length=2000)
    cost_drivers: list[str] = Field(min_length=1)
    optimization_recommendations: list[str] = Field(min_length=1)


class StructuredGenerationResult(BaseModel):
    summary: str = Field(min_length=1, max_length=5000)
    assumptions: list[str] = Field(min_length=1)
    architecture: Architecture
    assets: list[GeneratedFile] = Field(min_length=1)
    security_findings: list[SecurityFinding] = Field(min_length=1)
    zero_trust: ZeroTrust
    cost_guidance: CostGuidance


class GenerationRequest(BaseModel):
    """Input handed to a provider."""

    project_name: str
    description: str | None = None
    original_prompt: str | None = None
    prompt_override: str | None = None
    cloud_target: str = "azure"
    environment: str = "development"
    region: str = "eastus"
    availability_requirement: str = "standard"
    compliance_framework: str = "none"


SYSTEM_PROMPT = """You are a senior cloud and infrastructure-as-code architect.

Generate a complete, modular, readable cloud project for the user's request and
return ONLY a single JSON object that exactly matches the required schema.

Rules you must follow:
- Write modular, readable code with meaningful names and variables.
- NEVER place secrets, keys, tokens, or passwords in any file. Reference
  managed identities or external secret stores instead.
- Use managed identities and least-privilege access everywhere.
- Use private connectivity (private endpoints, private subnets, no public
  ingress) for production environments.
- Explain every assumption you make in the assumptions list.
- Do not fabricate cloud services or API versions that do not exist.
- Pin versions with explicit constraints where the ecosystem supports it.
- Use no destructive defaults (no `terraform destroy` helpers, no open deletes).
- Never emit code meant to be executed blindly; all artifacts are for review.
- Cost information is guidance only, never billing advice.
- Compliance notes are readiness guidance only, never certification.
- Return ONLY the required JSON schema. No markdown fences, no commentary.

The JSON schema you must produce:
{
  "summary": "string",
  "assumptions": ["string"],
  "architecture": {
    "overview": "string",
    "components": [{"name": "string", "purpose": "string"}],
    "traffic_flow": ["string"]
  },
  "assets": [
    {
      "asset_type": "one of: terraform, bicep, arm, cloudformation, kubernetes, helm, github-actions, azure-devops, jenkins, gitlab-ci, architecture, deployment, security, zero-trust, cost, readme",
      "file_name": "string (safe file name, e.g. main.tf)",
      "language": "string (e.g. hcl, yaml, markdown)",
      "content": "string (complete file content)"
    }
  ],
  "security_findings": [
    {
      "severity": "one of: critical, high, medium, low, informational",
      "title": "string",
      "description": "string",
      "recommendation": "string"
    }
  ],
  "zero_trust": {
    "identity_score": 0-100,
    "network_score": 0-100,
    "data_score": 0-100,
    "workload_score": 0-100,
    "overall_score": 0-100,
    "recommendations": ["string"]
  },
  "cost_guidance": {
    "disclaimer": "string",
    "cost_drivers": ["string"],
    "optimization_recommendations": ["string"]
  }
}

You MUST emit all 16 asset types: terraform, bicep, arm, cloudformation,
kubernetes, helm, github-actions, azure-devops, jenkins, gitlab-ci,
architecture, deployment, security, zero-trust, cost, readme.
"""
