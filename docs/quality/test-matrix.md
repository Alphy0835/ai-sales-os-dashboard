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
| API integration | Django `TestCase` | `apps/api/**/tests/` | **109** (3 skipped on SQLite) | `api`, `api-postgres` |
| Web unit | Vitest | `apps/web/src/lib/__tests__/` | **23** | `web` (`npm run test:unit`) |
| E2E | Playwright | `apps/web/e2e/*.spec.ts` | **2** specs | `e2e` |
| Web lint | ESLint | `apps/web` | — | `web` (`npm run lint`) |
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
| Google Sheets CRM | `integrations/tests/test_google_sheets_sync.py` | 5 | CrmLead upsert, selective ClientToReview rules |
| Source sync API | `integrations/tests/test_source_sync_api.py` | 1 | manual sync trigger (`force=True`) |
| P4c CRM query | `integrations/tests/test_crm_query.py` | 6 | scoped filters, vocabulary |
| P4c sync throttle | `integrations/tests/test_sync_throttle.py` | 5 | interval skip, force bypass |
| P4c agent CRM | `ai/tests/test_agent_crm.py` | 3 | NL→query, `as_of` in reply |
| Cross-tenant IDOR | `core/tests/test_tenant_idor.py` | 5 | agent CRM, source sync, recordings |
| Registration | `accounts/tests/test_registration.py` | 6 | invite validation, tenant binding |
| Login throttle | `accounts/tests/test_auth_throttle.py` | 1 | 429 on login rate limit |
| Agent throttle | `ai/tests/test_agent_throttle.py` | 1 | 429 on agent rate limit |
| LLM throttles | `ai/tests/test_llm_throttles.py` | 3 | analytics run, custom report, upload |
| Upload validation | `integrations/tests/test_upload_validation.py` | 2 | size/extension edge cases |
| LLM fallback | `ai/tests/test_llm_fallback.py` | 1 | rule-based fallback without API key |

### Web unit tests

| File | Tests | Focus |
|---|---|---|
| `auth.test.ts` | 5 | profile cache, home routes |
| `api.test.ts` | 10 | login/logout cookies, refresh on 401, `authFetch`, register |
| `dashboard.test.ts` | 4 | manager/employee dashboard query builders |
| `reviews.test.ts` | 4 | review list/create/task update |

## Test Types

Unit · Integration (API) · E2E · Manual smoke · Security regression · Migration check

## Environments

| Environment | Automated suites | Manual |
|---|---|---|
| local | API 109 + Vitest 23 + optional E2E 2 | UI polish |
| CI (GitHub Actions) | API + api-postgres + lint + Vitest + E2E 2 + build + migrations | — |
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
| GAP-001 | Auth | Cross-tenant IDOR (2 tenants) | high | Expand `test_tenant_idor` (remaining endpoints) | partial |
| GAP-002 | Web lint | `npm run lint` not in CI | medium | Add to CI web job (P3-D4 T7) | closed |
| GAP-003 | E2E | Employee flow + logout | low | Second Playwright spec (P3-D4 T8) | open |
| GAP-004 | Vitest | `dashboard.ts`, `reviews.ts` query builders | low | Unit tests (P3-D4 T9) | open |
| GAP-005 | Throttle | 429 login/agent/LLM tests | medium | `test_auth_throttle`, `test_agent_throttle`, `test_llm_throttles` | partial |
| GAP-006 | Upload | Size/extension edge cases | medium | P3-D4 T5 | open |
| GAP-007 | P4c CRM | Query service, sync throttle, agent CRM tool | medium | P4c-8 tests | closed |

## Related Docs

- [testing-strategy.md](testing-strategy.md)
- [release-checklist.md](release-checklist.md)
- [acceptance-criteria.md](acceptance-criteria.md)
