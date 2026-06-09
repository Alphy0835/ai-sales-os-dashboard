Doc ID: SECURITY-CHECKLIST-001
Status: active
Source of truth: yes
Owner: security
Related docs: docs/security/threat-model.md, docs/security/auth-and-access-control.md, docs/operations/deployment.md, docs/quality/release-checklist.md
Update together with: threat-model.md, auth-and-access-control.md, deployment.md
Update trigger: новый security control, auth change, или pre-release review
Review required: security, backend, frontend (release owner)
Maturity: L2

# Security Checklist

Pre-release checklist for AI Sales OS. Use before production deploys and when shipping auth, permissions, AI, or integration features.

**Legend:** `[x]` implemented and verified in codebase · `[ ]` gap or post-MVP

## Auth / Access

- [x] **Module permissions enforced on every view** — `ModulePermission` checks per module; maps to `/auth/me/` (`apps/api/accounts/permissions.py`, feature views)
- [x] **Manager scope hierarchy** — `ManagerScope`, subset-of-parent rule, `scope.py`; 403 + audit on violation
- [x] **Ceiling rule on permission grants** — grantor cannot exceed own level (`accounts/services/grant.py`, REQ-014)
- [x] **Knowledge article per-user grants** — `KnowledgeArticleGrant` + PAGE-006 Access tab (`ai/services/knowledge_grants.py`, `permissions-api.ts`)
- [x] **JWT refresh on 401** — `authFetch` + `refreshAccessToken()` (`apps/web/src/lib/api.ts`)
- [x] **Login / refresh rate limiting** — `LoginRateThrottle`, default `10/min` (`THROTTLE_LOGIN`); disabled in tests
- [x] **Agent chat rate limiting** — `AgentRateThrottle`, default `30/min` (`THROTTLE_AGENT`)
- [ ] **httpOnly cookie auth** — MVP uses `localStorage`; see [threat-model.md](threat-model.md) T1
- [ ] **Refresh token blacklist / server logout** — not implemented

## Multi-tenant Isolation

- [x] **All tenant querysets filter `user.tenant_id`** — enforced in views/services, not custom managers (see [data-model.md](../architecture/data-model.md))
- [x] **Detail endpoints check tenant + scope** — `can_access_recording`, `resolve_client`, `_get_target` patterns
- [x] **AI scope isolation regression tests** — `ai/tests/test_security_scope.py` (reports + agent context + 404 session)
- [x] **No raw SQL** — ORM only

## Data

- [x] **Sensitive data classified** — [data-classification.md](data-classification.md), transcripts = confidential
- [x] **Secrets not in repo** — `.env` gitignored; [secrets-management.md](secrets-management.md)
- [x] **Logs exclude passwords and tokens** — [audit-logging.md](audit-logging.md) "Not Logged" section
- [x] **Transcript retention 90 days** — `TRANSCRIPT_RETENTION_DAYS`, Celery `integrations.purge_expired_transcripts`, `manage.py purge_transcripts`
- [x] **Audio not persisted** — transcripts/metadata only; see [data-retention.md](data-retention.md)
- [x] **LLM keys encrypted at rest** — Fernet in Django Admin (tenant/workspace OpenRouter keys)

## API / Integration

- [x] **Input validation on uploads** — 100 MB max, audio extension whitelist (`integrations/serializers.py`, S4)
- [x] **Safe query param parsing** — audit `limit` fallback 50 (S6)
- [x] **Agent invalid session → 404** — not 500 (S5)
- [x] **OpenRouter keys documented** — [integrations.md](../architecture/integrations.md), Admin-only
- [ ] **Production STT provider** — ASR deferred; demo transcript in `content_json`

## Production Config

- [x] **Fail-fast prod settings** — `IS_PRODUCTION`, `SECRET_KEY` ≥32, `DEBUG=false` (`config/settings.py`)
- [x] **HSTS + secure cookies** — production Django security middleware
- [x] **WhiteNoise static** — prod static serving
- [x] **CI security regression** — `.github/workflows/ci.yml` (API tests + migration check + web build)
- [x] **Dependency lock + Dependabot** — `requirements.lock.txt`, `.github/dependabot.yml`
- [ ] **CSP headers** — not configured in repo
- [ ] **Sentry / structured JSON logging** — P2 §13

## Release

- [x] **Pre-deploy DB backup** — [deployment.md](../operations/deployment.md), [backup-and-restore.md](../operations/backup-and-restore.md)
- [x] **Rollback procedure documented** — [rollback.md](../operations/rollback.md)
- [x] **Incident runbook exists** — [incident-response.md](incident-response.md)
- [x] **Threat model current for JWT + tenant + S1–S6** — [threat-model.md](threat-model.md)
- [ ] **E2E Playwright smoke** — P2 §14
- [ ] **Monitoring alerts** — [monitoring-and-alerts.md](../operations/monitoring-and-alerts.md) not filled

## Quick Verification Commands

```bash
# API tests (includes scope security)
cd apps/api && python manage.py test

# Retention dry-run
python manage.py purge_transcripts --dry-run

# Prod migration status (on deploy host)
docker compose -f docker-compose.prod.yml exec api python manage.py showmigrations
```

## Related Docs

- [threat-model.md](threat-model.md)
- [auth-and-access-control.md](auth-and-access-control.md)
- [incident-response.md](incident-response.md)
- [../operations/deployment.md](../operations/deployment.md)
