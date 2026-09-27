"""Generation orchestration: runs the AI provider synchronously (MVP).

Flow:
  pending -> running -> succeeded | failed
On success the structured output is validated, rules-engine findings are
merged with AI findings, zero-trust scores are recomputed, and one
GeneratedAsset row is persisted per emitted file.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings
import logging

from app.core.logging_config import get_logger, log_extra
from app.core.security import sanitize_error_message
from app.models.generation import Generation
from app.models.asset import GeneratedAsset
from app.models.project import Project
from app.providers.azure_openai import AzureOpenAIProvider
from app.providers.base import AIProvider, ProviderError
from app.providers.demo import DemoProvider
from app.providers.schemas import GenerationRequest, StructuredGenerationResult
from app.services import security_rules, zerotrust

logger = get_logger(__name__)


def get_provider(settings: Settings) -> AIProvider:
    if settings.AI_PROVIDER == "azure_openai":
        return AzureOpenAIProvider(
            endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            deployment=settings.AZURE_OPENAI_DEPLOYMENT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
    return DemoProvider()


def validate_structured_output(data: object) -> StructuredGenerationResult:
    """Validate raw provider output; raise ProviderError if invalid."""
    try:
        return StructuredGenerationResult.model_validate(data)
    except ValidationError as exc:
        raise ProviderError(
            "Provider output failed schema validation: "
            + sanitize_error_message(str(exc.errors()[:3]))
        ) from exc


def run_generation(
    db: Session,
    *,
    project: Project,
    prompt_override: str | None,
    settings: Settings,
    provider: AIProvider | None = None,
) -> Generation:
    provider = provider or get_provider(settings)
    model_name = getattr(provider, "model", provider.name)

    generation = Generation(
        project_id=project.id,
        provider=provider.name,
        model=model_name,
        status="pending",
    )
    db.add(generation)
    db.commit()
    db.refresh(generation)

    project.status = "generating"
    generation.status = "running"
    generation.started_at = datetime.now(timezone.utc)
    db.commit()

    try:
        request = GenerationRequest(
            project_name=project.name,
            description=project.description,
            original_prompt=project.original_prompt,
            prompt_override=prompt_override,
            cloud_target=project.cloud_target,
            environment=project.environment,
            region=project.region,
            availability_requirement=project.availability_requirement,
            compliance_framework=project.compliance_framework,
        )
        result = provider.generate(request)
        # Defense in depth: re-validate the serialized output before persisting.
        result = validate_structured_output(result.model_dump())

        merged = _finalize_result(result)

        generation.structured_output = merged.model_dump()
        generation.status = "succeeded"
        generation.error_message = None
        generation.completed_at = datetime.now(timezone.utc)
        db.commit()

        _persist_assets(db, generation.id, merged)
        project.status = "ready"
        db.commit()
        db.refresh(generation)
        return generation
    except ProviderError as exc:
        return _fail_generation(
            db, generation, project, sanitize_error_message(str(exc))
        )
    except Exception:  # never leak internals
        log_extra(
            logger,
            logging.ERROR,
            "Unexpected generation failure",
            {"generation_id": generation.id},
        )
        return _fail_generation(
            db, generation, project, "Generation failed unexpectedly."
        )


def _fail_generation(
    db: Session, generation: Generation, project: Project, error_message: str
) -> Generation:
    generation.status = "failed"
    generation.error_message = error_message
    generation.completed_at = datetime.now(timezone.utc)
    project.status = "failed"
    db.commit()
    db.refresh(generation)
    return generation


def _finalize_result(result: StructuredGenerationResult) -> StructuredGenerationResult:
    """Merge rules-engine findings and recompute zero-trust scores."""
    triples = [(a.asset_type, a.file_name, a.content) for a in result.assets]
    rule_findings = security_rules.scan_assets(triples)
    ai_findings = [f.model_dump() for f in result.security_findings]
    merged_findings = security_rules.merge_findings(ai_findings, rule_findings)
    scores = zerotrust.compute_zero_trust(merged_findings)

    data = result.model_dump()
    data["security_findings"] = merged_findings
    data["zero_trust"] = scores
    return StructuredGenerationResult.model_validate(data)


def _persist_assets(
    db: Session, generation_id: str, result: StructuredGenerationResult
) -> None:
    for asset in result.assets:
        content_hash = hashlib.sha256(asset.content.encode("utf-8")).hexdigest()
        db.add(
            GeneratedAsset(
                generation_id=generation_id,
                asset_type=asset.asset_type,
                file_name=asset.file_name,
                language=asset.language,
                content=asset.content,
                content_hash=content_hash,
            )
        )
    db.commit()
