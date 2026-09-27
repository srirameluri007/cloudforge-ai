# CloudForge AI

**From natural-language requirements to secure, validated, deployment-ready cloud infrastructure.**

CloudForge AI lets you describe cloud infrastructure in plain language — e.g.
*"Create an Azure virtual network with three subnets for AKS, Application Gateway, and Azure Bastion.
Add NSGs, diagnostics, private endpoints, required tags, and a GitHub Actions deployment pipeline."* —
and generates structured, reviewable outputs: Terraform, Bicep, ARM templates, CloudFormation,
Kubernetes manifests, Helm charts, CI/CD pipelines (GitHub Actions, Azure DevOps, Jenkins, GitLab CI),
architecture docs, security and Zero Trust assessments, cost guidance, and deployment instructions.

> **Important:** Generated infrastructure is a starting point. It must be reviewed by a qualified
> engineer before deployment. Cost figures are guidance, not billing estimates. Compliance output is
> readiness guidance, not certification.

---

## Features

- Natural-language infrastructure prompts with configurable cloud target, environment, region,
  availability, and compliance framework
- 16 output tabs: Architecture, Terraform, Bicep, ARM, CloudFormation, Kubernetes, Helm,
  GitHub Actions, Azure DevOps, Jenkins, GitLab CI, Deployment, Security, Zero Trust, Cost, README
- Syntax-highlighted code viewer, copy-to-clipboard, per-file download, full-project ZIP export
- AI provider abstraction: **Azure OpenAI** (primary) + deterministic **DemoProvider** (no key needed)
- Rules-based security review + Zero Trust scoring on every generation
- JWT authentication via HTTP-only cookies, organizations with tenant isolation
- Audit logging (admin-visible), credential-reference vault (metadata only — never raw secrets)
- Docker Compose for the full stack; Alembic migrations; pytest / Vitest / Playwright tests

## Architecture overview

```
┌──────────────┐      HTTPS/JSON       ┌──────────────┐      SQLAlchemy      ┌────────────┐
│  Next.js 14  │  ──────────────────►  │   FastAPI    │  ─────────────────►  │ PostgreSQL │
│  frontend    │  ◄──────────────────  │   backend    │                     │    16      │
│  :3000       │   HttpOnly cookie     │   :8000      │                     └────────────┘
└──────────────┘                       └──────┬───────┘
                                             │ REST (JSON mode)
                                      ┌──────┴────────┐
                                      │ Azure OpenAI  │  or DemoProvider
                                      │  (optional)   │  (deterministic, offline)
                                      └───────────────┘
```

See [docs/architecture.md](docs/architecture.md) for details.

## Prerequisites

- Docker + Docker Compose (for the containerized stack), **or**
- Node.js 20+, Python 3.12 (for native development)
- An Azure OpenAI deployment **only** if you want live AI generation; the demo provider needs nothing.

## Quick start (Docker, demo mode)

```bash
cp .env.example .env
docker compose -f docker-compose.demo.yml up --build
```

Then open:

| Service | URL |
|---|---|
| App | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| Readiness | http://localhost:8000/ready |

**Demo credentials** (seeded automatically in demo mode): `demo@example.com` / `DemoPass123!`

For a non-demo compose stack: `docker compose up --build` (reads `.env`; set `AI_PROVIDER=azure_openai`
plus `AZURE_OPENAI_*`, or `AI_PROVIDER=openai` plus `OPENAI_API_KEY`, for live generation).

## Native development (no Docker)

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
```

Configure the database (PostgreSQL must be running):

```bash
export DATABASE_URL="postgresql+psycopg://cloudforge:cloudforge@localhost:5432/cloudforge"
export JWT_SECRET="a-long-random-secret"
export AI_PROVIDER=demo
alembic upgrade head
python -m app.seed --force   # optional: seeds demo@example.com / DemoPass123!
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm ci
npm run dev   # http://localhost:3000 (expects API at NEXT_PUBLIC_API_URL, default http://localhost:8000)
```

## AI provider configuration

| Variable | Meaning |
|---|---|
| `AI_PROVIDER=demo` | Deterministic local provider. No network, no key. All outputs are clearly labeled demo-generated. |
| `AI_PROVIDER=azure_openai` | Live generation via Azure OpenAI chat completions (JSON mode, 90s timeout, Pydantic-validated). |
| `AI_PROVIDER=openai` | Live generation via OpenAI chat completions (JSON mode, 90s timeout, Pydantic-validated). |

Azure OpenAI additionally requires: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`,
`AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`. The OpenAI provider
requires `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`, default `gpt-4o-mini`).
API keys never reach the browser.

## Environment variables

See [.env.example](.env.example) for the full list. Key notes:

- `JWT_SECRET` **must** be set to a random value; the app refuses to boot in `APP_ENV=production`
  with a missing/default secret.
- `SEED_DEMO=true` seeds the demo organization + user (demo compose sets this).
- `COOKIE_SECURE=true` in production (requires HTTPS).
- `DATABASE_URL` uses the `postgresql+psycopg://` SQLAlchemy scheme.

## Database migrations

```bash
cd backend
alembic upgrade head        # apply
alembic downgrade -1        # roll back one revision
alembic revision --autogenerate -m "description"   # create a new revision after model changes
```

## Tests

```bash
cd backend && pytest -q            # 41 tests (health, auth, projects, generations, assets, audit, credentials, security rules, export)
cd frontend && npm test             # 12 Vitest tests
cd frontend && npx playwright test   # e2e smoke (needs the stack running on :3000/:8000)
```

CI (`.github/workflows/ci.yml`) runs backend lint/format/typecheck/tests against PostgreSQL 16,
frontend lint/typecheck/tests/build, compose config validation, image builds, and a gitleaks secret scan.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `alembic` can't connect | Check `DATABASE_URL`; ensure Postgres is up (`pg_isready`). |
| Login fails with seeded user | Confirm `SEED_DEMO=true` ran (or `python -m app.seed --force`); use `demo@example.com`. |
| Frontend can't reach API | Set `NEXT_PUBLIC_API_URL` to the backend origin; check CORS `FRONTEND_URL` on the backend. |
| Generation fails with Azure provider | Verify `AZURE_OPENAI_*` vars and deployment name; check backend logs for the sanitized error; retry. |
| Port 8000/3000 busy | Stop the other process or change the compose port mapping. |

## Security warnings

- **Never paste raw cloud credentials, API keys, or secrets into prompts or credential fields.**
  Credential references store only a vault pointer (e.g. `keyvault://...`); raw-secret-looking values
  are rejected with HTTP 422 and the attempt is audited.
- Generated code is guidance: review it, run `terraform plan`, and scan it before applying.
- Rotate `JWT_SECRET` if ever exposed; keep `.env` out of version control (it is gitignored).

## Current MVP limitations

- Generation is synchronous (large prompts may take up to the provider timeout).
- Rate limiting is in-memory (resets on restart; use a gateway/Redis in production).
- No direct cloud deployment, credential rotation, SSO, or compliance certification —
  these are future extension points (see [docs/roadmap.md](docs/roadmap.md)).
- DemoProvider output is illustrative, not production-ready.

## Deploy to production (Render)

Prerequisites: a Render account and an OpenAI API key
(platform.openai.com → Billing → API keys).

1. In the Render dashboard: **New → Blueprint**, select the `cloudforge-ai` repo
   (this applies `render.yaml`: managed Postgres + `cloudforge-ai-api` + `cloudforge-ai-web`).
2. After apply, open the `cloudforge-ai-api` service → Environment → set
   `OPENAI_API_KEY` manually (it is `sync: false`, so Render will not ask for it
   during Blueprint apply).
3. Deploy. The API runs Alembic migrations automatically on boot; `JWT_SECRET`
   is auto-generated.

Resulting URLs:

| Service | URL |
|---|---|
| App | https://cloudforge-ai-web.onrender.com |
| API | https://cloudforge-ai-api.onrender.com |

The browser talks same-origin to the web service; `/api/*` is proxied server-side
to the API, so session cookies stay first-party (no CORS issues). Rotate
`JWT_SECRET` in the Render dashboard if it is ever exposed.

## Production deployment considerations

- Terminate TLS at a reverse proxy; set `COOKIE_SECURE=true`, `APP_ENV=production`.
- Use a managed PostgreSQL with backups; run `alembic upgrade head` on deploy.
- Put the app behind a WAF/rate-limiting gateway; set `FRONTEND_URL` to the exact origin.
- Store `AZURE_OPENAI_API_KEY` and `JWT_SECRET` in a real vault (Key Vault / Secrets Manager),
  injected as environment variables — never in the image.
- Ship logs to a central aggregator; alert on 5xx and `auth.login.failure` spikes.

## License

MIT — see [LICENSE](LICENSE).
