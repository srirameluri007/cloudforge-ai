# CloudForge AI — Backend

FastAPI backend for CloudForge AI: multi-tenant cloud project generation with a
pluggable AI provider (deterministic demo provider included), a static security
rules engine, zero-trust scoring, ZIP export, and full audit logging.

## Requirements

- Python 3.12
- PostgreSQL 15+ (production / CI)
- SQLite is used automatically only for the local test suite (see below)

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # if provided; otherwise export the vars below
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` / `test` / `production`. In `production`, startup fails if `JWT_SECRET` is missing/default or `FRONTEND_URL` contains `*`. |
| `APP_NAME` | `CloudForge AI` | Service name. |
| `FRONTEND_URL` | `http://localhost:3000` | Comma-separated CORS allow-list. |
| `BACKEND_URL` | `http://localhost:8000` | Public backend URL. |
| `DATABASE_URL` | `postgresql+psycopg://cloudforge:cloudforge@localhost:5432/cloudforge` | SQLAlchemy URL. Alembic reads `DATABASE_URL` from the environment too. |
| `JWT_SECRET` | `change-me-in-production` | HMAC secret for auth cookies. **Must** be set in production. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Cookie lifetime. |
| `AI_PROVIDER` | `demo` | `demo` (deterministic, no network) or `azure_openai`. |
| `AZURE_OPENAI_ENDPOINT` | `` | e.g. `https://my-resource.openai.azure.com` |
| `AZURE_OPENAI_API_KEY` | `` | Azure OpenAI key (never logged, never persisted). |
| `AZURE_OPENAI_DEPLOYMENT` | `` | Chat-completions deployment name. |
| `AZURE_OPENAI_API_VERSION` | `2024-12-01-preview` | API version. |
| `LOG_LEVEL` | `INFO` | JSON structured logging; secrets are redacted. |
| `SEED_DEMO` | `false` | Seed `Demo Organization` + `demo@example.com` / `DemoPass123!`. |
| `COOKIE_SECURE` | `false` | Set `true` in production (HTTPS). |

## Migrations

```bash
# upgrade to latest
alembic upgrade head
# downgrade one step
alembic downgrade -1
```

Alembic uses `DATABASE_URL` from the environment (see `alembic/env.py`).

## Running

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Or via Docker (runs `alembic upgrade head`, optional seed, then uvicorn with
`--proxy-headers`):

```bash
docker build -t cloudforge-backend .
docker run --env-file .env -p 8000:8000 cloudforge-backend
```

Set `SEED_DEMO=true` to seed the demo org/admin on container start.

## Tests

```bash
pytest -q
```

**Local test database:** the suite overrides the `get_db` dependency with a
file-based SQLite database (`tmp_path`), because a PostgreSQL server may not
exist in every dev environment. The Alembic round-trip test
(`test_alembic_upgrade_downgrade_upgrade`) also runs against SQLite locally.
**CI and docker-compose run the identical suite against PostgreSQL** — set
`DATABASE_URL` to the Postgres URL; migrations are written to be portable
(no Postgres-specific column types).

## Quality gates

```bash
ruff format --check .
ruff check .
mypy app
pytest -q
# migration round-trip against the test DB:
DATABASE_URL="sqlite:////tmp/gate.db" alembic upgrade head \
  && DATABASE_URL="sqlite:////tmp/gate.db" alembic downgrade -1 \
  && DATABASE_URL="sqlite:////tmp/gate.db" alembic upgrade head
```

## API overview

All routes live under `/api/v1` except `GET /health` and `GET /ready`.
Auth uses an HttpOnly `access_token` cookie (JWT, claims `sub`/`org`/`exp`).
Errors use the envelope `{"error": {"code", "message", "fields?", "request_id"}}`.

- `POST /api/v1/auth/register` · `POST /api/v1/auth/login` ·
  `POST /api/v1/auth/logout` · `GET /api/v1/auth/me`
- `POST/GET/PATCH/DELETE /api/v1/projects…` (tenant-isolated; cross-org → 404)
- `POST /api/v1/projects/{id}/generate` (synchronous MVP run)
- `GET /api/v1/projects/{id}/generations` · `GET /api/v1/generations/{id}` ·
  `POST /api/v1/generations/{id}/retry`
- `GET /api/v1/generations/{id}/assets` · `GET /api/v1/assets/{id}` ·
  `GET /api/v1/assets/{id}/download` · `GET /api/v1/generations/{id}/export` (ZIP)
- `GET /api/v1/audit-events` (org admin only)
- `POST/GET/DELETE /api/v1/credential-references` (metadata only; raw secrets → 422)
- `PATCH /api/v1/users/me` · `DELETE /api/v1/users/me`
- `GET /api/v1/settings/ai-provider`

### MVP limitations (documented)

- The auth rate limiter (`/api/v1/auth/*`, 60 req/min per IP) is in-memory and
  per-process; use a distributed store (e.g. Redis) in production.
- Generation runs synchronously in the request; move to a background worker
  for long-running providers.
