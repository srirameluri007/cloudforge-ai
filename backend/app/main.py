"""FastAPI application factory, middleware, routers, exception handlers."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1 import (
    assets,
    audit,
    auth,
    credentials,
    generations,
    projects,
    settings as settings_api,
    users,
)
from app.core.config import get_settings
import logging

from app.core.logging_config import (
    configure_logging,
    get_logger,
    get_request_id,
    log_extra,
)
from app.core.middleware import (
    RequestIdMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.ratelimit import RateLimitMiddleware
from app.database.session import get_db
from app.schemas.common import error_envelope

settings = get_settings()
configure_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)


def _origins() -> list[str]:
    return [o.strip() for o in settings.FRONTEND_URL.split(",") if o.strip()]


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

    # RequestIdMiddleware is added last so it runs first (outermost): early
    # rejections (413/429) still carry a request id.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            content = detail
        else:
            code = {
                400: "bad_request",
                401: "unauthorized",
                403: "forbidden",
                404: "not_found",
                409: "conflict",
                413: "payload_too_large",
                422: "validation_error",
                429: "rate_limited",
            }.get(exc.status_code, "error")
            content = error_envelope(code, str(detail), get_request_id() or "")
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields: dict[str, list[str]] = {}
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", []))
            fields.setdefault(loc, []).append(err.get("msg", "Invalid value."))
        content = error_envelope(
            "validation_error",
            "Request validation failed.",
            get_request_id() or "",
            fields,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=content
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        log_extra(
            logger, logging.ERROR, "Unhandled exception", {"path": request.url.path}
        )
        content = error_envelope(
            "internal_error", "An unexpected error occurred.", get_request_id() or ""
        )
        return JSONResponse(status_code=500, content=content)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": settings.APP_VERSION}

    @app.get("/ready")
    def ready(db: Session = Depends(get_db)) -> JSONResponse:
        try:
            db.execute(text("SELECT 1"))
        except Exception:
            log_extra(logger, logging.ERROR, "Readiness check failed")
            return JSONResponse(
                status_code=503,
                content=error_envelope(
                    "not_ready", "Database unavailable.", get_request_id() or ""
                ),
            )
        return JSONResponse(status_code=200, content={"status": "ready"})

    api = "/api/v1"
    app.include_router(auth.router, prefix=api)
    app.include_router(projects.router, prefix=api)
    app.include_router(generations.router, prefix=api)
    app.include_router(assets.router, prefix=api)
    app.include_router(audit.router, prefix=api)
    app.include_router(credentials.router, prefix=api)
    app.include_router(users.router, prefix=api)
    app.include_router(settings_api.router, prefix=api)

    return app


app = create_app()
