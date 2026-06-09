Doc ID: QA-DOD-001
Status: active
Source of truth: yes
Owner: QA
Related docs: docs/quality/release-checklist.md, docs/quality/test-matrix.md, docs/quality/acceptance-criteria.md, docs/security/security-checklist.md, docs/operations/integrator-vps-pilot.md
Update together with: release-checklist.md, test-matrix.md, acceptance-criteria.md
Update trigger: new stage shipped, CI gate change, pilot gate change
Review required: QA, product, release owner
Maturity: L2

# Definition of Done

A feature, stage, or pilot release is **done** when all applicable items below are satisfied. Use per PR/stage for development; use the full list before VPS pilot Go.

## Per feature / PR

- [ ] **Requirements linked** — REQ/STAGE ID in PR or commit; behavior matches `docs/project/product-requirements.md`
- [ ] **Acceptance criteria** — related QA-AC entries updated or marked `passed` in [acceptance-criteria.md](acceptance-criteria.md)
- [ ] **Code + tests pass CI** — API tests, migrations check, web lint, build, Vitest, E2E green on `main` (see [test-matrix.md](test-matrix.md))
- [ ] **Automated tests added** — new behavior covered by API and/or Vitest tests where practical; no regression in tenant scope or auth
- [ ] **Docs updated** — feature doc in `docs/features/` or architecture/operations doc if API, deploy, or integrator steps changed
- [ ] **Security impact checked** — relevant items in [security-checklist.md](../security/security-checklist.md) reviewed; threat model updated if auth, tenant, or AI surface changed
- [ ] **No open critical bugs** — per [severity-matrix.md](severity-matrix.md)

## Before VPS pilot release (integrator Go)

- [ ] **P0 code blockers closed** — Admin BFF proxy, LLM/STT throttles, Redis throttle cache (see [review.md](../../review.md))
- [ ] **Prod secrets on host** — `DJANGO_SECRET_KEY`, `AI_CREDENTIALS_KEY`, `POSTGRES_PASSWORD`, `ALLOWED_HOSTS`, `CORS` per `.env.example` and [deployment.md](../operations/deployment.md)
- [ ] **Integrator runbook exists and followed** — [integrator-vps-pilot.md](../operations/integrator-vps-pilot.md) end-to-end for tenant #1
- [ ] **DPA / tenant consent** — OpenRouter processing of transcripts/KB documented and agreed before real PII ([data-processing-agreement.md](../legal/data-processing-agreement.md))
- [ ] **Release checklist complete** — [release-checklist.md](release-checklist.md) Before Release + Post-Deploy Smoke
- [ ] **DB backup taken** — [backup-and-restore.md](../operations/backup-and-restore.md)
- [ ] **Rollback path known** — [rollback.md](../operations/rollback.md)
- [ ] **Pilot QA sign-off** — manual pass on QA-AC-001–004 (dashboard, clients to review) or documented exceptions

## Production polish (P5 — optional before full prod)

- [ ] **Basic CSP headers** — partial: Next.js `headers()` in `apps/web/next.config.ts`; tighten `script-src` when dev `unsafe-eval` no longer needed
- [ ] **Sentry / structured alerts** — env-gated error reporting (P5-2)
- [ ] **Staging environment** — smoke before VPS deploy
- [ ] **Monitoring alerts** — [monitoring-and-alerts.md](../operations/monitoring-and-alerts.md) filled and wired

## Stage completion (STAGE-001–007)

| Stage | Done when |
|---|---|
| STAGE-001 | Auth, scope, permissions, cookie JWT; QA-AC-013/014 passed |
| STAGE-002 | Integration sources, recordings, STT path; QA-AC-015/016 verified for pilot scope |
| STAGE-003 | Manager dashboard + clients to review; QA-AC-001–004 pilot sign-off |
| STAGE-004 | Reviews and tasks; QA-AC-005/006 passed |
| STAGE-005 | Analytics criteria and reports; QA-AC-007/008 passed |
| STAGE-006 | Knowledge base, agent chat, grants; QA-AC-010–012 passed |
| STAGE-007 | Custom reports; QA-AC-009 passed |

## Related Docs

- [release-checklist.md](release-checklist.md)
- [test-matrix.md](test-matrix.md)
- [acceptance-criteria.md](acceptance-criteria.md)
- [security-checklist.md](../security/security-checklist.md)
- [integrator-vps-pilot.md](../operations/integrator-vps-pilot.md)
