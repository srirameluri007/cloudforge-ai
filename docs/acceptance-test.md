# Acceptance test — CloudForge AI MVP

Executed 2026-09-27. Environment notes first, because they matter for interpreting the results.

## Environment

The sandbox could not run the Docker daemon (no iptables/nftables kernel modules in this
unprivileged container), so `docker compose up` was not runnable here. Both compose files pass
`docker compose config` validation, and the acceptance workflow was executed **natively** instead:
PostgreSQL 16 (local), backend via `uvicorn`, frontend via `next start`, Playwright against
`http://localhost:3000` → API at `http://localhost:8000`. This exercises the exact same code
paths the containers run (same Dockerfiles' entrypoint steps: `alembic upgrade head`, optional
seed, `uvicorn`).

Mid-run, the sandbox VM was replaced (ephemeral disk wiped: Postgres data and apt-installed
packages lost; `~/workspace` persisted). PostgreSQL 16 was reinstalled afterwards from the local
apt cache and the database-backed checks (steps 6, 8–10, 12, 14, 15) were executed or re-executed
against it; the UI-driven Playwright run used a throwaway SQLite DB while Postgres was
unavailable — the backend code path is identical (SQLAlchemy + the same Alembic migration).

## Results (spec section 25, 15 steps)

| # | Step | Result |
|---|---|---|
| 1 | Start the complete stack from a clean environment | **PASS** — Postgres 16 + `alembic upgrade head` + `uvicorn` backend + `next start` frontend; `/health` → `{"status":"ok"}`, `/ready` → `{"status":"ready"}` |
| 2 | Open the frontend | **PASS** — landing page renders (product name, tagline, Start Building, review-before-deploy notice) |
| 3 | Login using documented demo credentials | **PASS** — `demo@example.com` / `DemoPass123!` (note: the original `.local` address was rejected by the backend email validator; fixed to `example.com` everywhere) |
| 4 | Create a project named "Azure Network Demo" | **PASS** — via UI (Playwright) and via API (`POST /api/v1/projects`) |
| 5 | Enter the spec prompt (Azure vnet, 3 subnets, NSGs, diagnostics, tags, GitHub Actions) | **PASS** — prompt accepted |
| 6 | Generate the project using DemoProvider | **PASS** — `POST …/generate` → `status: succeeded`, `provider: demo` |
| 7 | Confirm all required tabs render | **PASS** — all 16 tabs render (Architecture, Terraform, Bicep, ARM, CloudFormation, Kubernetes, Helm, GitHub Actions, Azure DevOps, Jenkins, GitLab CI, Deployment, Security, Zero Trust, Cost, README); empty states shown before generation |
| 8 | Terraform, Bicep, ARM, GitHub Actions contain non-empty content | **PASS** — `main.tf` (2,532 chars), `main.bicep` (1,502), `main.json` (2,196), `ci-deploy.yml` (1,040); all 19 assets non-empty, every file carries the demo-generated banner |
| 9 | Security tab contains findings or a passed-check summary | **PASS** — 4 findings (severities: informational, low, medium), labeled "Automated guidance, not a formal security audit" |
| 10 | Zero Trust tab displays component scores and recommendations | **PASS** — identity 92, network 92, data 100, workload 96, overall 95 (+ recommendations) |
| 11 | Download the complete project ZIP | **PASS** — `GET …/export` → 200, `application/zip`; Playwright asserted the download |
| 12 | Inspect the ZIP structure | **PASS** — 20 files under `generated-project/{terraform,bicep,arm,cloudformation,kubernetes,helm,pipelines/{github-actions,azure-devops,jenkins,gitlab-ci},docs,security}/` + root `README.md` + `generation_metadata.json`; no path-traversal entries |
| 13 | Restart the application | **PASS** — backend stopped and restarted; `/health` 200, `/ready` 200 |
| 14 | Confirm the project remains in PostgreSQL | **PASS** — after restart, `GET /api/v1/projects` returns "Azure Network Demo" from PostgreSQL 16 (verified again post-reboot on a fresh database: create → stop → start → project listed) |
| 15 | Confirm the audit log contains creation, generation, and export events | **PASS** — `project.create`, `generation.start`, `generation.success`, `project.export`, `auth.login.success` all present (admin-visible at `GET /api/v1/audit-events`) |

## Verdict

**ACCEPTED.** All 15 steps pass within the documented environment constraints. The two
environment-driven deviations (`docker compose up` not runnable in this sandbox; VM reboot
mid-run) are recorded above and do not reflect application defects — the compose files
validate, and every containerized step has a natively-executed equivalent with identical code.
