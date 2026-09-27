"""In-memory per-IP rate limiter middleware (documented MVP limitation).

Applies to /api/v1/auth/* routes only: 60 requests/minute per client IP.
Exceeding the limit returns 429 with the standard error envelope.

This is intentionally simple for the MVP: state lives in a single process and
does not survive restarts or scale across workers. A production deployment
should use a distributed store (e.g. Redis) with a proper token-bucket.
"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.logging_config import get_request_id

RATE_LIMIT = 60
WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, app: object, limit: int = RATE_LIMIT, window_seconds: int = WINDOW_SECONDS
    ):
        super().__init__(app)  # type: ignore[arg-type]
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        return client.host if client else "unknown"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not request.url.path.startswith("/api/v1/auth/"):
            return await call_next(request)
        key = self._client_key(request)
        now = time.monotonic()
        with self._lock:
            window_start = now - self.window_seconds
            hits = [t for t in self._hits[key] if t > window_start]
            if len(hits) >= self.limit:
                self._hits[key] = hits
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "rate_limited",
                            "message": "Too many requests. Please try again later.",
                            "request_id": get_request_id() or "",
                        }
                    },
                )
            hits.append(now)
            self._hits[key] = hits
        return await call_next(request)
