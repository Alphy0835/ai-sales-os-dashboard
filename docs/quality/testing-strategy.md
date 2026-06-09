Doc ID: QA-TEST-001
Status: active
Source of truth: yes
Owner: Engineering
Related docs: definition-of-done.md, release-checklist.md, test-matrix.md
Update together with: CI workflow, apps/web/package.json test scripts
Update trigger: new critical user flows or auth/API contract changes
Review required: yes
Maturity: MVP

# Testing Strategy

## Purpose

Ensure regressions are caught before release across the Django API, Next.js BFF, and manager-facing flows. Automated tests cover business logic and auth; E2E validates the demo manager journey end-to-end.

## Test Levels

| Level | Tool | Location | When it runs |
|---|---|---|---|
| API integration | Django `TestCase` | `apps/api/**/tests/` | CI job `api` |
| Web unit | Vitest | `apps/web/src/lib/__tests__/` | CI job `web` |
| E2E | Playwright | `apps/web/e2e/` | CI job `e2e` |
| Manual | Checklist | `release-checklist.md` | Pre-release |

## What Must Be Tested

- **Auth & session**: cookie-based login, refresh on 401, logout (`auth.ts`, `api.ts` unit tests).
- **Multi-tenant / scope**: API security tests (`test_security_scope.py`, permission views).
- **Manager critical path** (E2E): login → dashboard → create review → run AI analytics → canvas visible.
- **Migrations**: `makemigrations --check` in CI.

## What Can Be Tested Manually

- Visual polish, responsive layout, accessibility spot-checks.
- ASR / real telephony integrations (deferred from MVP).
- Production deploy, backup/restore, and monitoring alerts.

## Release-Critical Checks

1. `python manage.py test` (API)
2. `npm run build` + `npm run test:unit` (web)
3. Playwright manager flow (`npm run test:e2e`) with demo seeds
4. Smoke login on staging with demo credentials

### Local E2E setup

```bash
# Terminal 1 — API (SQLite, eager Celery)
cd apps/api
export CELERY_TASK_ALWAYS_EAGER=true
python manage.py migrate && python manage.py seed_demo seed_integrations seed_ai seed_dashboard
python manage.py runserver 8000

# Terminal 2 — Web BFF
cd apps/web
API_BACKEND_URL=http://localhost:8000 npm run build && npm run start

# Terminal 3 — Playwright
cd apps/web
npm run test:e2e
```

Demo credentials: `manager@demo.local` / `demo1234`.

## Related Docs

- [Definition of Done](./definition-of-done.md)
- [Release checklist](./release-checklist.md)
- [Acceptance criteria](./acceptance-criteria.md)
