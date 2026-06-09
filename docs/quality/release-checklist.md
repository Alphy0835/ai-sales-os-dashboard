Doc ID: QA-RELEASE-001
Status: active
Source of truth: yes
Owner: QA
Related docs: docs/quality/testing-strategy.md, docs/quality/test-matrix.md, docs/security/security-checklist.md, docs/operations/deployment.md, docs/operations/integrator-vps-pilot.md, docs/operations/rollback.md, .github/workflows/ci.yml
Update together with: test-matrix.md, security-checklist.md, deployment.md
Update trigger: CI gate change, deploy process change, new release requirement
Review required: QA, operations, security
Maturity: L2

# Release Checklist

Use before staging pilot and every production deploy. CI must be green on `main` (or release branch) before Go.

## CI Gates (`.github/workflows/ci.yml`)

| Gate | Job | Command | Required |
|---|---|---|---|
| API tests (103) | `api`, `api-postgres` | `python manage.py test` | **yes** |
| Migration check | `api`, `api-postgres` | `python manage.py makemigrations --check --dry-run` | **yes** |
| Web lint | `web` | `npm run lint` | **yes** |
| Web build | `web` | `npm run build` | **yes** |
| Vitest unit (23) | `web` | `npm run test:unit` | **yes** |
| Playwright E2E (2) | `e2e` | `npm run test:e2e` (demo seeds + API + dev server) | **yes** |

Local parity before push:

```bash
cd apps/api && python manage.py test
cd apps/web && npm run lint && npm run build && npm run test:unit
```

## Before Release

- [ ] Requirements linked to shipped stages (STAGE-001–007)
- [ ] Feature docs updated (`docs/features/`)
- [ ] Acceptance criteria checked (`docs/quality/acceptance-criteria.md`)
- [ ] **CI green:** API tests (103), migrations, lint, web build, Vitest (23), E2E (2), api-postgres
- [ ] **Security checklist** reviewed ([security-checklist.md](../security/security-checklist.md))
- [ ] **Deployment notes** current ([deployment.md](../operations/deployment.md)) — BFF env: `NEXT_PUBLIC_API_URL=""`, `API_BACKEND_URL=http://api:8000`
- [ ] **Integrator runbook** reviewed for pilot ([integrator-vps-pilot.md](../operations/integrator-vps-pilot.md))
- [ ] **Rollback notes** ready ([rollback.md](../operations/rollback.md))
- [ ] **DB backup** taken ([backup-and-restore.md](../operations/backup-and-restore.md))
- [ ] No open **critical** bugs ([severity-matrix.md](severity-matrix.md))
- [ ] Env vars verified on target host (`.env` from `.env.example`)

## Post-Deploy Smoke

- [ ] `GET /api/v1/health/ready/` → 200 (through BFF + TLS)
- [ ] Django Admin reachable at `https://<domain>/admin/` (BFF proxy)
- [ ] Login with pilot credentials (not demo seeds in prod)
- [ ] Manager dashboard loads
- [ ] Celery worker + beat running (`purge_expired_transcripts` scheduled)
- [ ] One write path (e.g. create review or run analytics)

## Release Notes

_(fill per release)_

## Known Risks

- ASR / real telephony connectors deferred (demo transcript path)
- Dashboard hero KPI empty/partial with Google Sheets-only CRM (expected — see integrator runbook)
- Basic CSP headers in Next.js BFF (partial — P5-1); Sentry not configured (P5-2)
- JWT httpOnly cookies reduce XSS token theft; XSS can still drive same-origin API calls

## Go / No-Go Decision

All **P0 blockers** must be closed before pilot Go. See [review.md](../../review.md) and [integrator-vps-pilot.md](../operations/integrator-vps-pilot.md).

| P0 | Gate | Verified by |
|---|---|---|
| P0-1 | Django Admin доступен через BFF (`/admin/`) | Integrator |
| P0-2 | Prod secrets в `.env` (`DJANGO_SECRET_KEY`, `AI_CREDENTIALS_KEY`, `POSTGRES_PASSWORD`, `ALLOWED_HOSTS`, `CORS`) | Ops |
| P0-3 | LLM/STT throttle на heavy endpoints | QA / backend |
| P0-4 | DPA/согласие tenant на OpenRouter до реальных PII | Legal / integrator |
| P0-5 | Integrator runbook выполнен (`docs/operations/integrator-vps-pilot.md`) | Integrator |

| Role | Name | Decision | Date |
|---|---|---|---|
| Release owner | | Go / No-Go | |
| QA | | Go / No-Go | |
| Security | | Go / No-Go | |
| Integrator | | Go / No-Go | |

## Related Docs

- [test-matrix.md](test-matrix.md)
- [testing-strategy.md](testing-strategy.md)
- [definition-of-done.md](definition-of-done.md)
- [integrator-vps-pilot.md](../operations/integrator-vps-pilot.md)
