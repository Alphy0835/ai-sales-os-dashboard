Doc ID: SECURITY-THREAT-001
Status: active
Source of truth: yes
Owner: security
Related docs: docs/security/auth-and-access-control.md, docs/security/data-retention.md, docs/architecture/data-model.md, review.md
Update together with: auth-and-access-control.md, data-model.md, security-checklist.md
Update trigger: новая фича с PII, деньгами, ролями или внешним API; изменение auth storage; scope/tenant изменения
Review required: security, backend, frontend
Maturity: L2

# Threat Model

Модель угроз для User Level MVP (Django API + Next.js web). Обновлять при добавлении ASR, httpOnly auth, новых интеграций или enterprise-фич.

## Scope

| In scope | Out of scope (MVP) |
|---|---|
| JWT auth, module permissions, manager scope | Integration Level (Django Admin session) |
| Multi-tenant row isolation (`tenant_id`) | Physical infra hardening beyond prod settings |
| Transcripts, KB, AI agent context | Payment / billing flows |
| OpenRouter LLM + pgvector RAG | Real CRM/telephony connectors |

## Assets

| Asset | Sensitivity | Location |
|---|---|---|
| JWT access + refresh tokens | critical | Browser `localStorage` (`apps/web/src/lib/auth.ts`) |
| User credentials (password hash) | critical | PostgreSQL |
| Conversation transcripts + metadata | confidential | PostgreSQL (90d retention) |
| Knowledge base + embeddings | confidential | PostgreSQL (`VectorField` on PostgreSQL prod) |
| LLM API keys (tenant/workspace) | critical | Django Admin, Fernet-encrypted |
| Audit log (permissions, scope denied) | internal | PostgreSQL |

Audio is **not persisted** — only derived transcript text (ASR deferred).

## Trust Boundaries

```
[Browser / localStorage JWT] ──HTTPS──▶ [Next.js] ──▶ [Django API + ORM]
                                              │
                    tenant_id + scope filters in every view/queryset
                                              │
                                              ▼
                                    [PostgreSQL] [Redis/Celery]
                                              │
                                              └──▶ [OpenRouter LLM] (prompt excerpts only)
```

## Threat Actors

| Actor | Goal | Typical vector |
|---|---|---|
| External attacker | Steal tokens, brute-force login, IDOR | XSS, credential stuffing, API abuse |
| Malicious tenant user | Access another tenant's or out-of-scope data | Forged IDs, scope bypass in AI/report endpoints |
| Compromised manager | Escalate permissions beyond ceiling | `PUT /permissions/users/{id}/` abuse |
| Insider / ops | Exfiltrate DB backup | Unrestricted backup file access |

## STRIDE Summary

| Category | Primary risks | Mitigations (implemented) |
|---|---|---|
| Spoofing | Stolen JWT, brute-force login | JWT expiry; `LoginRateThrottle` 10/min on login/refresh (`THROTTLE_LOGIN`); password hashing |
| Tampering | Cross-tenant ID manipulation | All querysets filter `user.tenant_id`; detail views use scope helpers |
| Repudiation | Denied permission changes | `AuditLog` for permission changes and scope-denied |
| Information disclosure | Scope leak via AI agent/reports; XSS token theft | S1/S2 fixes; React escaping (no `dangerouslySetInnerHTML`); see JWT section |
| Denial of service | Login/agent flood | Login + agent throttles; file upload size/type limits (S4) |
| Elevation of privilege | Grant broader permissions than grantor | Ceiling rule in `grant.py`; KB per-user grants |

## Critical Scenarios

### T1 — XSS → JWT theft (localStorage)

| | |
|---|---|
| **Threat** | Any XSS in the web app can read `localStorage` and exfiltrate access + refresh tokens. Attacker impersonates user until refresh token expires. |
| **Likelihood** | Medium (depends on future UI/libs) |
| **Impact** | High — full account access within tenant + scope |
| **Current controls** | React default escaping; no `dangerouslySetInnerHTML`; CSP not yet enforced in repo |
| **Accepted for MVP?** | Yes, with documented risk |
| **Target state (P2 item 18)** | httpOnly session cookies via BFF (Next.js route handlers proxy auth) or SameSite cookie + CSRF; refresh rotation + optional blacklist |

**Compensating controls until BFF:**

- Short access token lifetime (SimpleJWT defaults)
- Centralized `authFetch` with refresh on 401 (`apps/web/src/lib/api.ts`)
- No secrets in client bundle beyond public API URL
- Rate limits on auth endpoints
- Audit suspicious permission changes

### T2 — Cross-tenant data access

| | |
|---|---|
| **Threat** | Attacker with valid JWT for tenant A reads/writes tenant B rows. |
| **Likelihood** | Low (code-reviewed pattern) |
| **Impact** | Critical |
| **Controls** | Every tenant-scoped queryset filters by authenticated `user.tenant_id` in views/services — **not** via custom managers. `TenantMiddleware` sets `request.tenant` for convenience only (see C2 in review). Regression: 45 API tests including scope security tests. |

### T3 — Manager scope bypass (workspace hierarchy)

| | |
|---|---|
| **Threat** | Regional manager sees recordings/reports/transcripts outside assigned workspaces. |
| **Likelihood** | Medium before fixes; Low after S1/S2 |
| **Impact** | High (confidential conversation data) |
| **Controls** | `recordings_queryset(actor)`, `reports_queryset(actor)`, `can_access_recording`, scope checks on detail views; tests in `ai/tests/test_security_scope.py`. |

### T4 — Brute force / credential stuffing

| | |
|---|---|
| **Threat** | Automated login attempts against `/auth/login/`. |
| **Impact** | Medium |
| **Controls** | S3 fix: `LoginRateThrottle` on login + refresh; prod `THROTTLE_LOGIN=10/min`; disabled in tests. |

### T5 — Malicious file upload

| | |
|---|---|
| **Threat** | Oversized or non-audio files via integration upload. |
| **Impact** | Medium (DoS, storage abuse) |
| **Controls** | S4: 100 MB cap, extension whitelist (mp3/wav/ogg/m4a/flac/webm), `duration_seconds >= 0`. Audio not stored long-term. |

### T6 — Error handling information leak / instability

| | |
|---|---|
| **Threat** | Invalid IDs or params cause 500 or reveal internal state. |
| **Controls** | S5: unknown agent `session_id` → 404; S6: safe `limit` parsing on audit endpoint with fallback 50. |

## Security Fixes Reference (2026-06-09 audit)

| ID | Issue | Fix location |
|---|---|---|
| S1 | AI agent `_recording_context` tenant-only filter leaked cross-workspace transcripts | `ai/services/agent.py` → `recordings_queryset(actor)` |
| S2 | AI reports list tenant-wide for scoped managers | `ai/views.py` → `reports_queryset(actor)` |
| S3 | No login throttling | `accounts/views.py`, `config/settings.py` |
| S4 | Unvalidated audio upload | `integrations/serializers.py` |
| S5 | Agent chat 500 on bad session | `ai/services/agent.py`, `ai/views.py` |
| S6 | Audit `?limit=abc` → 500 | `accounts/views.py` |

## Auth Storage Decision

| Approach | MVP (now) | Production target |
|---|---|---|
| Token storage | `localStorage` access + refresh | httpOnly Secure cookies via BFF |
| Refresh flow | Client `refreshAccessToken()` on 401 | Server-side refresh; optional rotation |
| Logout | Client clears storage | Server invalidates refresh (blacklist TBD) |
| XSS impact | Tokens readable by script | Cookies not readable by JS |

Document this tradeoff in release checklist until P2 item 18 is implemented.

## Residual Risks

| Risk | Owner | Mitigation plan |
|---|---|---|
| JWT in localStorage | frontend | httpOnly BFF (roadmap P2 §18) |
| No Sentry / centralized alerting | operations | P2 §13 |
| Agent chat / analytics indefinite retention | product | Policy in `data-retention.md` open questions |
| SQLite dev lacks vector search | backend | Keyword fallback only; prod uses pgvector |
| Backup contains full tenant DB | operations | Encrypt off-host backups; access control in `backup-and-restore.md` |

## Related Docs

- [auth-and-access-control.md](auth-and-access-control.md)
- [security-checklist.md](security-checklist.md)
- [incident-response.md](incident-response.md)
- [data-retention.md](data-retention.md)
- [../architecture/data-model.md](../architecture/data-model.md)
