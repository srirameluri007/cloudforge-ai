# Roadmap

Future extension points. These are **not** implemented in the MVP — the code contains
explicit seams for them, and nothing below is falsely claimed as working.

## Near term

- **Async generation worker** — move provider calls off the request thread (Celery/dramatiq +
  Redis, or Postgres-backed queue). The `Generation.status` field and `/retry` endpoint are
  the seam; the frontend already polls.
- **More AI providers** — add Anthropic/OpenAI-compatible providers behind the existing
  `AIProvider` interface (`AI_PROVIDER` env switch).
- **Real vault integration** — implement the `SecretStore` interface against Azure Key Vault,
  AWS Secrets Manager, or HashiCorp Vault. `CredentialReference` already stores only vault URIs.
- **Cost API integration** — plug official cloud pricing APIs behind a new `PricingProvider`
  interface; keep all numbers labeled as estimates.

## Medium term

- **Direct deployment (opt-in)** — `terraform plan/apply` from the backend with explicit user
  approval per run, full audit, and dry-run defaults. Never automatic.
- **Credential rotation** — scheduled rotation for service principals / deploy keys with audit.
- **Compliance checks** — CIS/NIST/SOC 2/PCI-DSS/ISO 27001 rule packs as data, versioned
  separately from the engine; output remains "readiness guidance", never certification.
- **SSO / MFA** — OIDC (Entra ID, Okta) and TOTP/WebAuthn behind the auth service seam.
- **Collaboration** — project sharing, comments, and approval workflows within an organization.

## Longer term

- **GitOps export** — push generated projects to a Git repository / open pull requests.
- **Drift detection** — scheduled `terraform plan` against live state with alerting.
- **Policy-as-code** — OPA/Conftest evaluation of generated templates before download.
- **Multi-tenancy hardening** — per-org encryption keys, tamper-evident audit log (hash-chained).

## Non-goals

- Fully autonomous infrastructure changes without human approval.
- Storing raw cloud credentials anywhere in the platform.
- Certifying compliance or guaranteeing cloud bills.
