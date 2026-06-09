Doc ID: PROJECT-ROADMAP-001
Status: draft
Source of truth: yes
Owner: product
Related docs: docs/project/product-requirements.md, docs/quality/acceptance-criteria.md, docs/quality/definition-of-done.md, docs/quality/release-checklist.md
Update together with: docs/project/product-requirements.md, docs/quality/acceptance-criteria.md
Update trigger: добавление этапа, изменение порядка, статуса или linked requirements
Review required: product, QA
Maturity: L1

# Roadmap

Дорожная карта User Level MVP. Каждый этап связан с требованиями из `docs/project/product-requirements.md` и критериями приёмки из `docs/quality/acceptance-criteria.md`.

> При завершении этапа: обновить Status, создать `roadmap-<название-этапа>.md` с описанием реализации и ссылкой из этого файла.

## Roadmap Index

| Stage ID | Name | Status | Linked Requirements | MVP |
|---|---|---|---|---|
| STAGE-001 | Access & Permissions | **done** | REQ-013, REQ-014, REQ-NFR-001, REQ-NFR-004 | yes |
| STAGE-002 | Data Integration | **done** | REQ-015, REQ-016, REQ-NFR-002, REQ-NFR-003 | yes |
| STAGE-003 | Manager Dashboard | **done** | REQ-001, REQ-002, REQ-003, REQ-004 | yes |
| STAGE-004 | Review Cycle | **done** | REQ-005, REQ-006 | yes |
| STAGE-005 | Quality & AI Analytics | **done** | REQ-007, REQ-008 | yes |
| STAGE-006 | Knowledge Base & AI Agents | **done** | REQ-010, REQ-011, REQ-012 | yes |
| STAGE-007 | Custom AI Reports | planned | REQ-009 | no |

---

## Stage: STAGE-001 — Access & Permissions

**Status:** done

**Goal:** обеспечить авторизацию User Level, иерархию руководителей, делегирование прав и изоляцию данных по scope.

**Linked requirements:** REQ-013, REQ-014, REQ-NFR-001, REQ-NFR-004

**Linked features:** FEAT-001

**Linked docs:** `docs/architecture/api-contracts.md` (API-AUTH-*), `docs/architecture/data-model.md`, `docs/security/auth-and-access-control.md`

**Linked security checks:** `docs/security/security-checklist.md` — Auth / Access; `docs/security/audit-logging.md`

**Linked QA:** QA-AC-013, QA-AC-014, QA-AC-NFR-001, QA-AC-NFR-004

**Implementation (code):**
- `apps/api/accounts/` — Tenant, User, ModulePermission, ManagerScope, AuditLog, JWT
- `apps/api/accounts/services/` — scope, grant (ceiling rule), audit
- `apps/web/src/app/login/` — PAGE-001
- `apps/web/src/components/ProtectedShell.tsx` — manager/employee shells (stub pages)

**Done when:** *(all criteria met 2026-06-09)*
- Руководитель и сотрудник входят в User Level с разными наборами модулей.
- Правило потолка блокирует выдачу прав шире, чем у назначающего.
- Данные изолированы по scope; попытка доступа вне scope отклоняется.
- QA: automated tests in `accounts/tests/test_stage001.py`; formal QA-AC sign-off pending.

**Implementation doc:** [roadmap-access-permissions.md](roadmap-access-permissions.md)

---

## Stage: STAGE-002 — Data Integration

**Status:** done

**Goal:** подключить источники CRM, телефонии, отчётности и записи общений с транскрипцией для последующей аналитики.

**Linked requirements:** REQ-015, REQ-016, REQ-NFR-002, REQ-NFR-003

**Linked features:** FEAT-002

**Linked security checks:** `docs/security/secrets-management.md`; `docs/architecture/integrations.md`

**Linked QA:** QA-AC-015, QA-AC-016, QA-AC-NFR-002, QA-AC-NFR-003

**Release/rollback docs:** `docs/operations/deployment.md`, `docs/operations/rollback.md`, `docs/operations/monitoring-and-alerts.md`

**Done when:** *(backend MVP met 2026-06-09)*
- Показатели агрегируются из demo-источников через `GET /integrations/metrics/`.
- Записи — manual upload + demo telephony seed; транскрипции через Celery.
- `completeness: partial|empty` при degraded/disconnected источниках.
- Tests: `integrations/tests/test_stage002.py`.

**Implementation doc:** [roadmap-data-integration.md](roadmap-data-integration.md)

---

## Stage: STAGE-003 — Manager Dashboard

**Status:** done

**Goal:** дать руководителю сводку по подразделению, детализацию, AI-сигналы и список клиентов к разбору.

**Linked requirements:** REQ-001, REQ-002, REQ-003, REQ-004

**Linked features:** FEAT-003

**Linked security checks:** `docs/security/security-checklist.md` — Auth / Access (scope на дашборде)

**Linked QA:** QA-AC-001, QA-AC-002, QA-AC-003, QA-AC-004

**Release/rollback docs:** `docs/operations/deployment.md`, `docs/operations/rollback.md`

**Done when:** *(MVP met 2026-06-09)*
- PAGE-002 `/manager` — KPI, periods, trend, AI summary, employee table, sources.
- Drill-down: workspace + employee filters (REQ-002).
- PAGE-003 `/manager/clients` — clients to review (REQ-004).
- Employee `/employee` — personal metrics stub.
- Tests + `npm run build`.

**Implementation doc:** [roadmap-manager-dashboard.md](roadmap-manager-dashboard.md)

---

## Stage: STAGE-004 — Review Cycle

**Status:** **done**

**Goal:** замкнуть цикл разбора: фиксация разборов, постановка задач, отображение задач у сотрудника.

**Linked requirements:** REQ-005, REQ-006

**Linked features:** FEAT-004

**Linked security checks:** `docs/security/audit-logging.md` (создание/изменение разборов)

**Linked QA:** QA-AC-005, QA-AC-006

**Release/rollback docs:** `docs/operations/deployment.md`, `docs/operations/rollback.md`

**Done when:**
- Руководитель создаёт разбор с задачами; сотрудник видит задачи на личном дашборде.
- История разборов фильтруется по подразделению и сотруднику.
- Статус выполнения задач отражается в истории.
- FLOW-002 и FLOW-006 проходятся end-to-end.
- QA-AC этапа в статусе passed.

**Implementation doc:** [roadmap-review-cycle.md](roadmap-review-cycle.md)

---

## Stage: STAGE-005 — Quality & AI Analytics

**Status:** **done**

**Goal:** настроить критерии оценки качества и формировать AI-отчёты с канвасами по транскрипциям.

**Linked requirements:** REQ-007, REQ-008

**Linked features:** FEAT-005

**Linked security checks:** `docs/security/data-classification.md` (транскрипции и записи)

**Linked QA:** QA-AC-007, QA-AC-008

**Release/rollback docs:** `docs/operations/deployment.md`, `docs/operations/rollback.md`

**Done when:**
- Руководитель настраивает критерии оценки (при наличии прав).
- AI-аналитика формирует стандартный отчёт и канвас по сотруднику или подразделению.
- FLOW-003 проходится end-to-end при наличии транскрипций.
- QA-AC этапа в статусе passed.

**Implementation doc:** [roadmap-quality-ai-analytics.md](roadmap-quality-ai-analytics.md)

---

## Stage: STAGE-006 — Knowledge Base & AI Agents

**Status:** **done**

**Goal:** наполнить базу знаний и запустить AI-агентов для руководителя и сотрудника с учётом прав и RAG.

**Linked requirements:** REQ-010, REQ-011, REQ-012

**Linked features:** FEAT-006

**Linked security checks:** `docs/security/auth-and-access-control.md` (доступ к материалам RAG); `docs/security/data-classification.md`

**Linked QA:** QA-AC-010, QA-AC-011, QA-AC-012

**Release/rollback docs:** `docs/operations/deployment.md`, `docs/operations/rollback.md`

**Done when:**
- База знаний наполняется и влияет на ответы AI-агентов.
- Руководитель и сотрудник используют AI-агентов в рамках выданных прав.
- FLOW-005 и FLOW-007 проходятся end-to-end.
- Success Criteria MVP из product-requirements (п. 4) выполнен.
- QA-AC этапа в статусе passed.

**Implementation doc:** [roadmap-knowledge-ai-agents.md](roadmap-knowledge-ai-agents.md)

---

## Stage: STAGE-007 — Custom AI Reports

**Status:** planned

**Goal:** дать руководителю возможность описывать кастомные отчёты простым языком и повторно их запускать.

**Linked requirements:** REQ-009

**Linked features:** FEAT-007

**Linked security checks:** `docs/security/security-checklist.md` — Auth / Access

**Linked QA:** QA-AC-009

**Release/rollback docs:** `docs/operations/deployment.md`, `docs/operations/rollback.md`

**Done when:**
- Руководитель описывает кастомный отчёт; система сохраняет и позволяет повторный запуск в AI-аналитике.
- QA-AC-009 в статусе passed.

**Implementation doc:** — *(создаётся после завершения: `roadmap-custom-ai-reports.md`)*

---

## MVP Completion

User Level MVP считается завершённым после **STAGE-001 … STAGE-006** при выполнении Success Criteria из `docs/project/product-requirements.md`.

STAGE-007 — post-MVP улучшение, не блокирует первый релиз User Level.

## Related Docs

- `docs/project/product-requirements.md` — требования (REQ-...)
- `docs/quality/acceptance-criteria.md` — критерии приёмки (QA-AC-...)
- `docs/project/user-flow.md` — сценарии проверки этапов
- `docs/quality/definition-of-done.md` — Definition of Done
- `docs/quality/release-checklist.md` — чеклист перед релизом
