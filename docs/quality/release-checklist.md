Doc ID: QA-RELEASE-001
Status: active
Source of truth: yes
Owner: QA
Related docs: docs/quality/testing-strategy.md, docs/quality/test-matrix.md, docs/security/security-checklist.md, docs/operations/deployment.md, docs/operations/rollback.md, .github/workflows/ci.yml
Update together with: test-matrix.md, security-checklist.md, deployment.md
Update trigger: CI gate change, deploy process change, new release requirement
Review required: QA, operations, security
Maturity: L2

# Release Checklist

Use before staging pilot and every production deploy. CI must be green on `main` (or release branch) before Go.

## CI Gates (`.github/workflows/ci.yml`)

| Gate | Job | Command | Required |
|---|---|---|---|
| API tests (52) | `api` | `python manage.py test` | **yes** |
| Migration check | `api` | `python manage.py makemigrations --check --dry-run` | **yes** |
| Web build | `web` | `npm run build` | **yes** |
| Vitest unit (12) | `web` | `npm run test:unit` | **yes** |
| Playwright E2E (1) | `e2e` | `npm run test:e2e` (demo seeds + API + dev server) | **yes** |
| Web lint | — | `npm run lint` | **manual** (not yet in CI — see test-matrix GAP-002) |

Local parity before push:

```bash
cd apps/api && python manage.py test
cd apps/web && npm run build && npm run test:unit && npm run lint
```

## Before Release

- [ ] Requirements linked to shipped stages (STAGE-001–007)
- [ ] Feature docs updated (`docs/features/`)
- [ ] Acceptance criteria checked (`docs/quality/acceptance-criteria.md`)
- [ ] **CI green:** API tests, migrations, web build, Vitest, E2E
- [ ] **Security checklist** reviewed ([security-checklist.md](../security/security-checklist.md))
- [ ] **Deployment notes** current ([deployment.md](../operations/deployment.md)) — BFF env: `NEXT_PUBLIC_API_URL=""`, `API_BACKEND_URL=http://api:8000`
- [ ] **Rollback notes** ready ([rollback.md](../operations/rollback.md))
- [ ] **DB backup** taken ([backup-and-restore.md](../operations/backup-and-restore.md))
- [ ] No open **critical** bugs ([severity-matrix.md](severity-matrix.md))
- [ ] Env vars verified on target host (`.env` from `.env.example`)

## Post-Deploy Smoke

- [ ] `GET /api/v1/health/ready/` → 200 (through BFF + TLS)
- [ ] Login with demo/staging credentials
- [ ] Manager dashboard loads
- [ ] Celery worker + beat running (`purge_expired_transcripts` scheduled)
- [ ] One write path (e.g. create review or run analytics)

## Release Notes

_(fill per release)_

## Known Risks

- ASR / real telephony connectors deferred (demo transcript path)
- `npm run lint` not enforced in CI yet
- CSP and Sentry not configured (P5)
- JWT httpOnly cookies reduce XSS token theft; XSS can still drive same-origin API calls

## Go / No-Go Decision

| Role | Name | Decision | Date |
|---|---|---|---|
| Release owner | | Go / No-Go | |
| QA | | Go / No-Go | |
| Security | | Go / No-Go | |

## Related Docs

- [test-matrix.md](test-matrix.md)
- [testing-strategy.md](testing-strategy.md)
- [definition-of-done.md](definition-of-done.md)
