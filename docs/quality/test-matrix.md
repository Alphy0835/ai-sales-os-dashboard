Doc ID: QA-TEST-MATRIX-001
Status: active
Source of truth: yes
Owner: QA
Related docs: docs/quality/testing-strategy.md, docs/quality/release-checklist.md, docs/quality/acceptance-criteria.md, .github/workflows/ci.yml
Update together with: testing-strategy.md, release-checklist.md, CI workflow
Update trigger: new feature / changed flow / changed API / changed security logic
Review required: QA, product, backend, frontend, security
Maturity: L2

# Test Matrix

## Purpose

Maps features and critical flows to automated tests, environments, and release gates. Counts verified 2026-06-10.

## Test Inventory (current)

| Suite | Tool | Location | Count | CI job |
|---|---|---|---|---|
| API integration | Django `TestCase` | `apps/api/**/tests/` | **78** (3 skipped on SQLite) | `api`, `api-postgres` |
| Web unit | Vitest | `apps/web/src/lib/__tests__/` | **12** | `web` (`npm run test:unit`) |
| E2E | Playwright | `apps/web/e2e/manager-critical-flow.spec.ts` | **1** spec | `e2e` |
| Migrations check | `makemigrations --check` | `apps/api` | — | `api` |
| Web build | `next build` | `apps/web` | — | `web`, `e2e` |

### API test modules

| Module | File | Tests | Focus |
|---|---|---|---|
| STAGE-001 auth/scope/permissions | `accounts/tests/test_stage001.py` | 8 | login, scope, ceiling, audit |
| Cookie auth | `accounts/tests/test_auth_cookies.py` | 2 | cookie refresh, logout blacklist |
| Health | `core/tests/test_health.py` | 6 | liveness, readiness |
| STAGE-002 integrations | `integrations/tests/test_stage002.py` | 5 | sources, metrics, recordings |
| STAGE-003 dashboard | `analytics/tests/test_stage003.py` | 5 | manager/employee dashboard |
| STAGE-004 reviews | `reviews/tests/test_stage004.py` | 7 | review CRUD, tasks |
| STAGE-005 analytics | `ai/tests/test_stage005.py` | 6 | criteria, report run |
| STAGE-006 knowledge/agents | `ai/tests/test_stage006.py` | 5 | KB, agent chat |
| STAGE-007 custom reports | `ai/tests/test_stage007.py` | 4 | custom report CRUD + run |
| KB grants | `ai/tests/test_knowledge_grants.py` | 4 | per-user grants, ceiling |
| AI scope security | `ai/tests/test_security_scope.py` | 4 | cross-workspace isolation |
| Agent retention | `ai/tests/test_agent_retention.py` | 1 | 90d purge |
| pgvector (PostgreSQL only) | `ai/tests/test_pgvector.py` | 3 | embed + vector search |
| STT transcription | `integrations/tests/test_stt_transcription.py` | 3 | OpenRouter STT + fallback |
| amoCRM sync | `integrations/tests/test_amocrm_sync.py` | 3 | CRM metrics + errors |
| Source sync API | `integrations/tests/test_source_sync_api.py` | 1 | manual sync trigger |

### Web unit tests

| File | Tests | Focus |
|---|---|---|
| `auth.test.ts` | 5 | profile cache, home routes |
| `api.test.ts` | 7 | login/logout cookies, refresh on 401, `authFetch` |

## Test Types

Unit · Integration (API) · E2E · Manual smoke · Security regression · Migration check

## Environments

| Environment | Automated suites | Manual |
|---|---|---|
| local | API 52 + Vitest 12 + optional E2E | UI polish |
| CI (GitHub Actions) | API + Vitest + E2E + build + migrations | — |
| staging / production | smoke only | login → dashboard → analytics |

## Coverage Matrix

| Feature ID | Feature | Criticality | Tests | Environment | Release Gate | Related Docs | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| FEAT-001 | Access & Permissions | high | api (`test_stage001`, `test_auth_cookies`), vitest (`api.test`, `auth.test`) | local, CI | yes | auth-and-access-control.md | backend | covered |
| FEAT-002 | Data Integration | high | api (`test_stage002`) | local, CI | yes | data-integration.md | backend | covered |
| FEAT-003 | Manager Dashboard | high | api (`test_stage003`), e2e (dashboard step) | local, CI | yes | manager-dashboard.md | fullstack | covered |
| FEAT-004 | Review Cycle | high | api (`test_stage004`), e2e (review step) | local, CI | yes | review-cycle.md | fullstack | covered |
| FEAT-005 | Quality & AI Analytics | high | api (`test_stage005`), e2e (analytics canvas) | local, CI | yes | quality-ai-analytics (roadmap) | backend | covered |
| FEAT-006 | Knowledge & AI Agents | high | api (`test_stage006`, `test_knowledge_grants`, `test_security_scope`) | local, CI | yes | knowledge-base-ai-agents.md | backend | covered |
| FEAT-007 | Custom AI Reports | medium | api (`test_stage007`) | local, CI | yes | custom-ai-reports.md | fullstack | covered |
| — | Health / readiness | high | api (`test_health`) | local, CI | yes | deployment.md | backend | covered |

## Critical Flows

| Flow ID | Flow | Related Features | Required Tests | Release Gate | Status |
|---|---|---|---|---|---|
| FLOW-001 | Обзор подразделения | FEAT-003 | api `test_stage003`, e2e dashboard | yes | covered |
| FLOW-002 | Разбор с сотрудником | FEAT-004 | api `test_stage004`, e2e review create | yes | covered |
| FLOW-003 | AI-аналитика | FEAT-005, FEAT-007 | api `test_stage005/007`, e2e canvas | yes | covered |
| FLOW-004 | Настройка системы | FEAT-001, FEAT-005–007 | api stage001/005/007, grants | partial | api covered; E2E settings tab manual |
| FLOW-005 | AI-агент руководителя | FEAT-006 | api `test_stage006` | no | api only |
| FLOW-006 | Личный дашборд | FEAT-003, FEAT-004 | api `test_stage003/004` | no | api only |
| FLOW-007 | AI-агент сотрудника | FEAT-006 | api `test_stage006` | no | api only |

## Gaps

| Gap ID | Area | Missing Coverage | Risk | Action | Status |
|---|---|---|---|---|---|
| GAP-001 | Auth | Cross-tenant IDOR (2 tenants) | high | Add dedicated test module (P3-D4 T2) | open |
| GAP-002 | Web lint | `npm run lint` not in CI | medium | Add to CI web job (P3-D4 T7) | open |
| GAP-003 | E2E | Employee flow + logout | low | Second Playwright spec (P3-D4 T8) | open |
| GAP-004 | Vitest | `dashboard.ts`, `reviews.ts` query builders | low | Unit tests (P3-D4 T9) | open |
| GAP-005 | Throttle | 429 login/agent tests | medium | P3-D4 T4 | open |
| GAP-006 | Upload | Size/extension edge cases | medium | P3-D4 T5 | open |

## Related Docs

- [testing-strategy.md](testing-strategy.md)
- [release-checklist.md](release-checklist.md)
- [acceptance-criteria.md](acceptance-criteria.md)
