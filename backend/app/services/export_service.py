"""In-memory ZIP export of a generation's assets.

Layout:
    generated-project/
        terraform/ bicep/ arm/ cloudformation/ kubernetes/ helm/
        pipelines/{github-actions,azure-devops,jenkins,gitlab-ci}/
        docs/ security/
        README.md
        generation_metadata.json

Filenames are sanitized (basename, dangerous characters stripped, extension
allow-list per asset type); entries that would traverse directories are
skipped and reported.
"""

from __future__ import annotations

import io
import json
import os
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime

import logging

from app.core.logging_config import get_logger, log_extra

logger = get_logger(__name__)

ASSET_DIRS: dict[str, str] = {
    "terraform": "terraform",
    "bicep": "bicep",
    "arm": "arm",
    "cloudformation": "cloudformation",
    "kubernetes": "kubernetes",
    "helm": "helm",
    "github-actions": "pipelines/github-actions",
    "azure-devops": "pipelines/azure-devops",
    "jenkins": "pipelines/jenkins",
    "gitlab-ci": "pipelines/gitlab-ci",
    "architecture": "docs",
    "deployment": "docs",
    "cost": "docs",
    "security": "security",
    "zero-trust": "security",
    "readme": ".",
}

ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    "terraform": {".tf"},
    "bicep": {".bicep"},
    "arm": {".json"},
    "cloudformation": {".yaml", ".yml"},
    "kubernetes": {".yaml", ".yml"},
    "helm": {".yaml", ".yml"},
    "github-actions": {".yaml", ".yml"},
    "azure-devops": {".yaml", ".yml"},
    "jenkins": {""},  # Jenkinsfile has no extension
    "gitlab-ci": {".yaml", ".yml"},
    "architecture": {".md"},
    "deployment": {".md"},
    "cost": {".md"},
    "security": {".md"},
    "zero-trust": {".md"},
    "readme": {".md"},
}


def sanitize_filename(file_name: str, asset_type: str) -> str | None:
    """Return a safe file name or None if the entry must be skipped."""
    raw = file_name.replace("\\", "/")
    # Reject anything that even attempts traversal or absolute paths.
    if raw.startswith("/") or any(segment == ".." for segment in raw.split("/")):
        return None
    base = os.path.basename(raw)
    if not base or base in (".", ".."):
        return None
    # Strip anything outside a conservative allow-list.
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    safe = safe.strip("._")
    if not safe or safe in (".", ".."):
        return None
    allowed = ALLOWED_EXTENSIONS.get(asset_type)
    if allowed is None:
        return None
    _, ext = os.path.splitext(safe)
    if ext.lower() not in allowed:
        return None
    return safe


@dataclass
class ExportAsset:
    asset_type: str
    file_name: str
    content: str


@dataclass
class ExportResult:
    data: bytes
    included: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def build_zip(
    assets: list[ExportAsset],
    *,
    metadata: dict[str, object],
) -> ExportResult:
    buffer = io.BytesIO()
    result = ExportResult(data=b"")
    used_paths: set[str] = set()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for asset in assets:
            safe_name = sanitize_filename(asset.file_name, asset.asset_type)
            directory = ASSET_DIRS.get(asset.asset_type)
            if safe_name is None or directory is None:
                log_extra(
                    logger,
                    logging.WARNING,
                    "Skipping unsafe export entry",
                    {"file_name": asset.file_name, "asset_type": asset.asset_type},
                )
                result.skipped.append(f"{asset.asset_type}:{asset.file_name}")
                continue
            arcname = (
                f"generated-project/{directory}/{safe_name}"
                if directory != "."
                else f"generated-project/{safe_name}"
            )
            # De-duplicate within the archive.
            stem, ext = os.path.splitext(arcname)
            counter = 1
            while arcname in used_paths:
                counter += 1
                arcname = f"{stem}-{counter}{ext}"
            used_paths.add(arcname)
            zf.writestr(arcname, asset.content)
            result.included.append(arcname)

        zf.writestr(
            "generated-project/generation_metadata.json",
            json.dumps(metadata, indent=2, default=str),
        )

    result.data = buffer.getvalue()
    return result


def build_metadata(
    *,
    provider: str,
    model: str,
    generation_id: str,
    project: dict[str, object],
    started_at: datetime | None,
    completed_at: datetime | None,
    assumptions: list[str],
) -> dict[str, object]:
    return {
        "provider": provider,
        "model": model,
        "generation_id": generation_id,
        "demo": provider == "demo",
        "started_at": started_at.isoformat() if started_at else None,
        "completed_at": completed_at.isoformat() if completed_at else None,
        "project": project,
        "assumptions": assumptions,
        "limitations": [
            "Generated artifacts are templates for review, not production-ready infrastructure.",
            "Validate all resource names, SKUs, regions, and network ranges before use.",
            "Cost information is guidance only, never billing advice.",
            "Compliance notes are readiness guidance only, never certification.",
            "Automated security guidance is not a formal security audit.",
        ],
    }


def sanitize_archive_filename(value: str) -> str:
    """Sanitize a value used inside the download filename."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", value)[:80] or "project"
