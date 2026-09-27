"""Tests for DATABASE_URL scheme normalization in app.core.config.

Render's managed Postgres exposes its connection string as ``postgres://``;
SQLAlchemy 2.x with the installed psycopg v3 driver requires the explicit
``postgresql+psycopg://`` dialect. The Settings validator rewrites the scheme
before validation.
"""

from app.core.config import Settings


def test_postgres_scheme_rewritten_to_psycopg() -> None:
    settings = Settings(DATABASE_URL="postgres://u:p@h:5432/db")
    assert settings.DATABASE_URL == "postgresql+psycopg://u:p@h:5432/db"


def test_bare_postgresql_scheme_gets_psycopg_driver() -> None:
    settings = Settings(DATABASE_URL="postgresql://u:p@h:5432/db")
    assert settings.DATABASE_URL == "postgresql+psycopg://u:p@h:5432/db"


def test_explicit_psycopg_scheme_untouched() -> None:
    url = "postgresql+psycopg://u:p@h:5432/db"
    assert Settings(DATABASE_URL=url).DATABASE_URL == url


def test_sqlite_url_untouched() -> None:
    url = "sqlite:///./test.db"
    assert Settings(DATABASE_URL=url).DATABASE_URL == url


def test_rewrite_is_idempotent() -> None:
    once = Settings(DATABASE_URL="postgres://u:p@h:5432/db").DATABASE_URL
    twice = Settings(DATABASE_URL=once).DATABASE_URL
    assert twice == "postgresql+psycopg://u:p@h:5432/db"
