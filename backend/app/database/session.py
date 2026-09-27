"""Engine + session factory, with FastAPI dependency."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

_engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite is for local dev/tests only; keep it single-connection friendly.
    _engine_kwargs = {"connect_args": {"check_same_thread": False}}

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)  # type: ignore[arg-type]
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
