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
| JWT access + refresh tokens | critical | httpOnly cookies (`access_token`, `refresh_token`) via BFF; profile cache only in `localStorage` (`apps/web/src/lib/auth.ts`) |
| User credentials (password hash) | critical | PostgreSQL |
| Conversation transcripts + metadata | confidential | PostgreSQL (90d retention) |
| Knowledge base + embeddings | confidential | PostgreSQL (`VectorField` on PostgreSQL prod) |
| LLM API keys (tenant/workspace) | critical | Django Admin, Fernet-encrypted |
| Audit log (permissions, scope denied) | internal | PostgreSQL |

Audio is **not persisted** — only derived transcript text (ASR deferred).

## Trust Boundaries

```
[Browser / httpOnly JWT cookies] ──HTTPS──▶ [Next.js BFF rewrites] ──▶ [Django API + ORM]
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
| Information disclosure | Scope leak via AI agent/reports; XSS session abuse | S1/S2 fixes; httpOnly cookies; React escaping (no `dangerouslySetInnerHTML`); see T1 |
| Denial of service | Login/agent flood | Login + agent throttles; file upload size/type limits (S4) |
| Elevation of privilege | Grant broader permissions than grantor | Ceiling rule in `grant.py`; KB per-user grants |

## Critical Scenarios

### T1 — XSS → session abuse

| | |
|---|---|
| **Threat** | XSS cannot read httpOnly JWT cookies, but could still drive authenticated requests from the victim browser or exfiltrate non-secret profile data in `localStorage`. |
| **Likelihood** | Medium (depends on future UI/libs) |
| **Impact** | High — actions as the victim within tenant + scope |
| **Current controls** | httpOnly `access_token` / `refresh_token` via BFF (`accounts/cookies.py`); refresh rotation + blacklist on logout; React default escaping; no `dangerouslySetInnerHTML`; CSP not yet enforced |
| **Accepted for MVP?** | Yes, with documented residual risk |
| **Further hardening** | CSP headers (P5-3); optional CSRF token for cookie-auth mutations |

**Compensating controls:**

- Short access token lifetime (SimpleJWT defaults)
- Centralized `authFetch` with refresh on 401 (`apps/web/src/lib/api.ts`)
- Server-side refresh blacklist on logout (`LogoutView`)
- Rate limits on auth endpoints
- Audit suspicious permission changes

### T2 — Cross-tenant data access

| | |
|---|---|
| **Threat** | Attacker with valid JWT for tenant A reads/writes tenant B rows. |
| **Likelihood** | Low (code-reviewed pattern) |
| **Impact** | Critical |
| **Controls** | Every tenant-scoped queryset filters by authenticated `user.tenant_id` in views/services — **not** via custom managers. `TenantMiddleware` sets `request.tenant` for convenience only (see C2 in review). Regression: 52 API tests including scope security and cookie auth tests. |

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

| Approach | MVP (now) | Notes |
|---|---|---|
| Token storage | httpOnly Secure cookies via BFF | `access_token`, `refresh_token`; SameSite=Lax |
| Refresh flow | Cookie-only refresh + rotation | `ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION` |
| Logout | Server blacklists refresh + clears cookies | `token_blacklist` app |
| Profile cache | `localStorage` user display fields only | No JWT in JS-accessible storage |
| XSS impact | JWT not readable by script | Residual: XSS can still invoke same-origin API as user |

## Residual Risks

| Risk | Owner | Mitigation plan |
|---|---|---|
| XSS-driven API abuse despite httpOnly cookies | frontend | CSP (P5-3); review third-party scripts |
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
