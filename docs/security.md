# Security

## Threat model

**Trust boundaries:**

1. Browser ↔ backend API (cookie-authenticated JSON; CORS allow-listed to `FRONTEND_URL`).
2. Backend ↔ PostgreSQL (private compose network; credentials via env, never in the image).
3. Backend ↔ Azure OpenAI (server-side only; API key never leaves the backend).
4. Backend ↔ user-supplied prompts (untrusted input; validated, size-limited, never executed).

**Protected assets:** user credentials, session cookies, JWT secret, generated project content,
audit log integrity, Azure OpenAI API key, database contents.

**Primary threats & mitigations:**

| Threat | Mitigation (implemented) |
|---|---|
| Credential theft | bcrypt-hashed passwords; HTTP-only `SameSite=Lax` cookies (`Secure` in prod); generic login errors |
| XSS token exfiltration | No tokens in JS/localStorage; output encoding via React; security headers (nosniff, DENY framing, referrer policy, CSP) |
| CSRF | SameSite=Lax cookies; state-changing endpoints expect JSON (no simple-form CSRF); logout clears cookie |
| Injection / oversized payloads | Pydantic validation everywhere; 2 MB request-size limit (413); safe ZIP filename sanitization + path-traversal prevention |
| Secret leakage | Secret-pattern scanner rejects raw secrets in credential references (422) and audits the attempt; no passwords/secrets in logs; `.env` gitignored; gitleaks in CI |
| Tenant data leakage | Every protected query scoped by `organization_id` from the JWT; cross-org → 404 |
| AI prompt/output abuse | Structured JSON contract validated with Pydantic before persistence; unvalidated output never rendered as trusted code; provider errors sanitized |
| Brute force | In-memory per-IP rate limit on `/api/v1/auth/*` (60/min → 429 with error envelope) |
| Information disclosure | Global exception handler returns the error envelope only; no stack traces to clients; request IDs for correlation |

## Implemented controls checklist

- [x] Argon2/bcrypt password hashing (bcrypt via passlib), enforced password policy (≥10 chars, upper/lower/digit/special)
- [x] JWT in HTTP-only cookies, expiring (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- [x] CORS allow-list (startup failure in production on wildcard)
- [x] Rate limiting (documented MVP: in-memory)
- [x] Security headers middleware; request-size limits; request-ID tracing; structured JSON logs
- [x] Audit logging for auth, projects, generations, downloads, exports, credential refs
- [x] CredentialReference stores vault pointers only (`secret_reference` is a URI, never a secret)
- [x] Pinned dependencies (`requirements.txt`, `package-lock.json`)

## Remaining MVP risks

1. **In-memory rate limiter** — resets on restart and doesn't share state across replicas.
2. **Synchronous generation** — a slow provider holds a worker; add timeouts (done: 90s) and a queue in production.
3. **No MFA / SSO** — password-only auth in the MVP.
4. **Audit log is not tamper-evident** — no hash-chaining; protect DB backups accordingly.
5. **DemoProvider output is illustrative** — clearly labeled, but a user could still copy-paste it blindly; the UI and README warn repeatedly.

## Production-hardening recommendations

- Terminate TLS at a reverse proxy; `COOKIE_SECURE=true`, `APP_ENV=production`.
- Move rate limiting to the gateway (or Redis-backed limiter); add CAPTCHA on login/register abuse.
- Add MFA (TOTP/WebAuthn) and SSO (OIDC) via the existing auth service seam.
- Use a managed Postgres with encryption at rest, automated backups, and private networking.
- Inject `JWT_SECRET` / `AZURE_OPENAI_API_KEY` from a vault at deploy time; rotate on a schedule.
- Run image vulnerability scans in CI; sign images; deploy with read-only filesystems and non-root users.
- Forward structured logs to a SIEM; alert on 5xx spikes and `auth.login.failure` bursts.
- Periodic penetration test of the cookie-auth flow and the ZIP export path.
