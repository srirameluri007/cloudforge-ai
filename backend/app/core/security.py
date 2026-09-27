"""Password hashing, password policy, JWT helpers, and raw-secret scanning."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext  # type: ignore[import-untyped]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def validate_password_policy(password: str) -> list[str]:
    """Return a list of policy violations (empty means the password is valid)."""
    errors: list[str] = []
    if len(password) < 10:
        errors.append("Password must be at least 10 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Password must contain at least one special character.")
    return errors


def create_access_token(
    user_id: str, organization_id: str, secret: str, expires_minutes: int
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "org": organization_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_access_token(token: str, secret: str) -> dict[str, Any]:
    return jwt.decode(token, secret, algorithms=["HS256"])


# Patterns that indicate a RAW secret value (never allowed in metadata/reference fields).
_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "aws_secret_key",
        re.compile(r"\baws[-_]?secret[-_]?access[-_]?key\b", re.IGNORECASE),
    ),
    (
        "azure_key",
        re.compile(r"\b[A-Za-z0-9+/]{80,}={0,2}\b"),
    ),  # placeholder, gated below
    (
        "generic_assignment",
        re.compile(r"(?i)\b(api[-_]?key|secret|token|passwd|pwd)\s*[:=]\s*\S+"),
    ),
    ("password_assignment", re.compile(r"(?i)\bpassword\s*[:=]\s*\S+")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]{16,}")),
    (
        "private_key",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    ),
    ("github_token", re.compile(r"\b(ghp|gho|github_pat)_[A-Za-z0-9]{16,}\b")),
    ("slack_token", re.compile(r"\bxox[bpas]-[A-Za-z0-9-]{10,}\b")),
]

# The long-base64 pattern above is too broad on its own; only flag it when the
# field name suggests it is a key/secret/token/password value.
_KEYLIKE_FIELD = re.compile(r"(?i)(key|secret|token|password|passwd|pwd|credential)")


def contains_raw_secret(values: dict[str, Any]) -> tuple[bool, str | None]:
    """Scan all string values for raw-secret patterns.

    Returns (detected, pattern_name).
    """
    for field_name, value in values.items():
        if value is None:
            continue
        text = str(value)
        for name, pattern in _SECRET_PATTERNS:
            if name == "azure_key":
                if _KEYLIKE_FIELD.search(field_name) and pattern.search(text):
                    return True, name
                continue
            if pattern.search(text):
                return True, name
    return False, None


def sanitize_error_message(message: str, max_length: int = 500) -> str:
    """Trim an error message and strip anything that looks like a credential."""
    cleaned = re.sub(
        r"(?i)\b(api[-_]?key|secret|token|password)\s*[:=]\s*\S+", r"\1=***", message
    )
    cleaned = re.sub(r"\bAKIA[0-9A-Z]{16}\b", "AKIA***", cleaned)
    return cleaned[:max_length].strip()
