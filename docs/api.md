# API reference

Base URL: `http://localhost:8000`. All routes below (except `/health`, `/ready`) require the
`access_token` HTTP-only cookie. All timestamps are UTC ISO-8601.

**Error envelope** (every 4xx/5xx):

```json
{ "error": { "code": "string", "message": "string", "fields": {"field": ["..."]}, "request_id": "string" } }
```

List responses are shaped `{ "items": [ ... ] }`.

## Authentication

| Method & path | Body | Notes |
|---|---|---|
| `POST /api/v1/auth/register` | `{name, email, password}` | Creates user + personal org (admin). 409 if email taken. 422 on weak password / bad email. Sets cookie. |
| `POST /api/v1/auth/login` | `{email, password}` | Generic `Invalid email or password.` on failure. Sets cookie. |
| `POST /api/v1/auth/logout` | — | Clears cookie. |
| `GET /api/v1/auth/me` | — | `{user, organization, role}`. 401 when unauthenticated. |

## Health

| Method & path | Response |
|---|---|
| `GET /health` | `{"status":"ok","version":"0.1.0"}` |
| `GET /ready` | `{"status":"ready"}` or 503 `{"error":...}` when the DB is unreachable |

## Projects

| Method & path | Body | Notes |
|---|---|---|
| `POST /api/v1/projects` | `{name*, description, original_prompt, cloud_target*, environment*, region*, availability_requirement*, compliance_framework*}` | `cloud_target`: `azure\|aws\|multi-cloud`; `environment`: `development\|test\|production`; `availability_requirement`: `standard\|high-availability\|multi-region`; `compliance_framework`: `none\|cis\|nist\|soc2\|pci-dss\|iso27001` |
| `GET /api/v1/projects` | — | Org-scoped list |
| `GET /api/v1/projects/{id}` | — | 404 for other orgs |
| `PATCH /api/v1/projects/{id}` | partial project fields | |
| `DELETE /api/v1/projects/{id}` | — | 204 |

## Generations

| Method & path | Notes |
|---|---|
| `POST /api/v1/projects/{id}/generate` | Body `{"prompt": "optional override"}`. Runs synchronously; returns the generation (`pending→running→succeeded\|failed`). |
| `GET /api/v1/projects/{id}/generations` | Generation history for the project |
| `GET /api/v1/generations/{id}` | Includes validated `structured_output` (summary, assumptions, architecture, assets metadata, security findings, zero-trust scores, cost guidance) |
| `POST /api/v1/generations/{id}/retry` | Creates a **new** generation from the same project |

## Assets & export

| Method & path | Notes |
|---|---|
| `GET /api/v1/generations/{id}/assets` | Asset list (metadata only) |
| `GET /api/v1/assets/{id}` | Asset including `content` |
| `GET /api/v1/assets/{id}/download` | File download (`Content-Disposition: attachment`, sanitized filename) |
| `GET /api/v1/generations/{id}/export` | In-memory ZIP (`application/zip`) with the `generated-project/` layout + `generation_metadata.json` |

Asset types: `architecture, terraform, bicep, arm, cloudformation, kubernetes, helm,
github-actions, azure-devops, jenkins, gitlab-ci, deployment, security, zero-trust, cost, readme`.

## Audit, credentials, users, settings

| Method & path | Notes |
|---|---|
| `GET /api/v1/audit-events` | Org **admin only**; 403 otherwise |
| `POST /api/v1/credential-references` | `{name, provider, auth_type, vault_reference, description}`. Values are scanned for raw-secret patterns → 422 on match. Providers: Azure, AWS, GitHub, GitLab, Azure DevOps, Jenkins, Kubernetes, Terraform Cloud |
| `GET /api/v1/credential-references` | List |
| `DELETE /api/v1/credential-references/{id}` | |
| `PATCH /api/v1/users/me` | `{name}` |
| `DELETE /api/v1/users/me` | Deletes the account |
| `GET /api/v1/settings/ai-provider` | `{provider, configured, demo_mode}` |

Interactive docs: http://localhost:8000/docs (Swagger UI) and `/redoc`.
