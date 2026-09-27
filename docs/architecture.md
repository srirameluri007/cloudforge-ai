# Architecture

## System overview

CloudForge AI is a monorepo with three runtime services:

```
                    ┌─────────────────────────────────────────┐
                    │              docker-compose              │
                    │                                         │
  user ──► :3000 ──►│ frontend (Next.js 14, App Router)       │
                    │    │  fetch, credentials:'include'       │
                    │    ▼                                    │
         ──► :8000 ──►│ backend (FastAPI + SQLAlchemy)        │
                    │    │  psycopg v3                         │
                    │    ▼                                    │
                    │ db (PostgreSQL 16)                      │
                    └─────────────────────────────────────────┘
                           │ (optional, server-side only)
                           ▼
                    Azure OpenAI (chat completions, JSON mode)
                    — or — DemoProvider (in-process, deterministic)
```

- **Frontend** (`frontend/`): Next.js 14 App Router, React 18, TypeScript strict, Tailwind CSS,
  Monaco editor (bundled locally, no runtime CDN). All API calls go through `lib/api.ts`
  with `credentials: 'include'`; the JWT lives in an HTTP-only cookie so JS never sees it.
- **Backend** (`backend/`): FastAPI app factory (`app/main.py`) with versioned routers under
  `/api/v1`, Pydantic v2 schemas, SQLAlchemy 2.x models, Alembic migrations, structured JSON logging.
- **Database**: PostgreSQL 16. All tables use UUID primary keys, UTC timestamps, explicit
  `ondelete` behavior, and indexes on common query fields (`email`, `organization_id`, `project_id`).

## Request lifecycle (generation)

1. `POST /api/v1/projects/{id}/generate` (authenticated, org-scoped).
2. `generation_service` creates a `Generation` row (`status=running`), audits `generation.start`.
3. The configured `AIProvider.generate()` produces a `StructuredGenerationResult`.
4. The result is validated against the Pydantic contract (`providers/schemas.py`).
   Invalid output → `status=failed`, sanitized `error_message`, audit `generation.failed`,
   and the UI offers Retry (which creates a *new* generation row).
5. `security_rules` + `zerotrust` engines scan the assets; findings merge with AI findings.
6. One `GeneratedAsset` row per file (sha256 `content_hash`), `status=succeeded`,
   audit `generation.success`.
7. The frontend polls `GET /api/v1/generations/{id}` (MVP uses synchronous generation;
   the status field exists for a future async worker).

## AI provider abstraction

`providers/base.py` defines `AIProvider.generate(request) -> StructuredGenerationResult`.

- `DemoProvider` — pure Python, no network. Builds all 16 asset types deterministically from
  the project parameters (cloud target, environment, region, availability, compliance).
  Every file carries a demo-generated banner. Used for local dev, tests, and CI.
- `AzureOpenAIProvider` — calls `{endpoint}/openai/deployments/{deployment}/chat/completions`
  with `response_format: {"type": "json_object"}`, 90s timeout, sanitized error mapping,
  and Pydantic validation before persistence. API keys stay server-side.

Switching is a single env var: `AI_PROVIDER=demo|azure_openai|openai`.

## Data model

| Entity | Purpose |
|---|---|
| `User` | identity; bcrypt password hash; active flag |
| `Organization` / `OrganizationMembership` | tenant boundary; roles `admin`/`member` |
| `Project` | user input: prompt + cloud target, environment, region, availability, compliance |
| `Generation` | one provider run: status, structured JSON output, sanitized errors |
| `GeneratedAsset` | one file: type, name, language, content, sha256 |
| `AuditEvent` | append-only action log (org-scoped) |
| `CredentialReference` | vault pointer metadata only — raw secrets are rejected |

All protected queries filter by `organization_id` from the JWT; cross-org access returns 404
(to avoid leaking existence).

## Key design decisions

- **UUIDs as `String(36)`** rather than Postgres-native UUID: keeps Alembic migrations portable
  (tests also run against SQLite locally); documented in `backend/README.md`.
- **HTTP-only cookie auth** (`SameSite=Lax`, `Secure` in production) instead of localStorage tokens:
  immune to XSS token theft; CSRF risk is mitigated by SameSite + JSON-only POST endpoints.
- **Synchronous generation** for the MVP: simpler to reason about and test; the `Generation.status`
  field and `/retry` endpoint are the seam for a future background worker.
- **Monaco bundled locally** (`frontend/scripts/copy-monaco.mjs`): no runtime CDN dependency,
  works offline; falls back to `<pre>` if the editor fails to load.
- **Terraform/HCL + Bicep highlighting**: Monaco has no built-in grammars; the UI maps to the
  nearest built-in language and labels the badge honestly (HCL, Bicep).

## Repository layout

```
cloudforge-ai/
├── frontend/          # Next.js app (app/, components/, lib/, tests/)
├── backend/           # FastAPI app (app/, alembic/, tests/)
├── docs/              # architecture, security, api, testing, acceptance-test, roadmap
├── .github/workflows/ # CI
├── docker-compose.yml / docker-compose.demo.yml
├── .env.example / Makefile / LICENSE
└── README.md
```
