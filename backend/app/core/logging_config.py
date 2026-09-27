"""JSON structured logging. Never log passwords or secrets."""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone

_request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

_REDACT_KEYS = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "set-cookie",
}


def set_request_id(request_id: str | None) -> None:
    _request_id_ctx.set(request_id)


def get_request_id() -> str | None:
    return _request_id_ctx.get()


def _redact(obj: object) -> object:
    if isinstance(obj, dict):
        return {
            k: ("***REDACTED***" if str(k).lower() in _REDACT_KEYS else _redact(v))
            for k, v in obj.items()
        }
    if isinstance(obj, (list, tuple)):
        return [_redact(v) for v in obj]
    return obj


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            redacted = _redact(extra)
            if isinstance(redacted, dict):
                payload.update(redacted)
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    # Keep uvicorn access logs flowing through the same handler
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_extra(
    logger: logging.Logger,
    level: int,
    message: str,
    fields: dict[str, object] | None = None,
) -> None:
    """Log with structured extra fields (surfaced in the JSON output)."""
    logger.log(level, message, extra={"extra_fields": fields or {}})
