# Testing

## Backend (`backend/`, pytest — 41 tests)

```bash
cd backend
pytest -q
```

Coverage: health/ready; registration (valid, invalid email, weak password, duplicate);
login (success sets HTTP-only cookie; generic error for unknown user and wrong password);
401 without cookie; project CRUD + cross-org 404 tenant isolation; demo generation end-to-end
(all 16 asset types, non-empty, demo banner in every file); invalid provider output →
failed generation with sanitized error; retry creates a new generation; asset list/get/download;
ZIP export layout + traversal sanitization (`../../evil.tf` is skipped); credential raw-secret
rejection (`AKIA…`, `password=…` → 422 + audited); audit events for register/login/project/generate/export.

Local runs use a SQLite override in `tests/conftest.py` (documented in `backend/README.md`);
CI runs the same suite against PostgreSQL 16. Alembic round-trip
(`upgrade head` → `downgrade -1` → `upgrade head`) is verified against PostgreSQL.

Other backend gates:

```bash
ruff check . && ruff format --check .   # lint + format
mypy app                                 # type check
```

## Frontend (`frontend/`, Vitest — 12 tests)

```bash
cd frontend
npm test          # vitest run
npm run lint      # next lint
npm run typecheck # tsc --noEmit
npm run build     # production build (must succeed with no backend calls)
```

Unit tests: login form validation + submit; register password mismatch / weak / success;
project form required fields; prompt < 20 chars rejected without API call; tab switching
(incl. keyboard) renders the right asset; copy button writes to clipboard with feedback;
API 422 surfaces the backend's error message.

## End-to-end (Playwright — 1 smoke spec)

```bash
# with the stack running (http://localhost:3000 + http://localhost:8000)
cd frontend && npx playwright test
```

`tests/e2e/smoke.spec.ts`: open app → login (`demo@example.com` / `DemoPass123!`, overridable
via `E2E_EMAIL`/`E2E_PASSWORD`) → create project "Azure Network Demo" → enter the spec prompt →
Generate → wait for `succeeded` → open Terraform, Security, README tabs → download the project
ZIP → assert zero console/page errors.

## Manual acceptance test

See [docs/acceptance-test.md](acceptance-test.md) for the executed 15-step workflow and results.

## CI

`.github/workflows/ci.yml`: backend job (lint, format, mypy, Alembic upgrade, pytest on PG 16,
gitleaks secret scan), frontend job (lint, typecheck, tests, build), docker job
(compose config validation + image builds). No production secrets required.
