Doc ID: FEAT-003
Status: done
Related requirements: REQ-001, REQ-002, REQ-003, REQ-004
Related user flows: FLOW-001
Related API: API-MGR-001, API-MGR-002, API-EMP-001 — `docs/architecture/api-contracts.md`
Related data model: ClientToReview — `docs/architecture/data-model.md`
Related security: FEAT-001 (scope)
Related tests: QA-AC-001, QA-AC-002, QA-AC-003, QA-AC-004
Update trigger: изменение метрик дашборда, AI-сводки или списка клиентов к разбору
Owner: product
Review required: product, design, frontend

# Manager Dashboard

## Purpose

Дать руководителю сводку по подразделению и сигналы для раннего контроля без переслушивания всех звонков.

## Description

- Главный дашборд (PAGE-002): сегодня, неделя, месяц, динамика, отставание от нормы.
- Drill-down по подразделению и сотруднику (REQ-002).
- AI-сводка: просадки, зоны внимания, кого контролировать/похвалить (REQ-003).
- Вкладка «Клиенты к разбору» (PAGE-003): список с обоснованием (REQ-004).
- **P4c:** `ClientToReview` populated only from explicit CRM rules (`needs_review` column / `review_rules` in Admin config) — not every open lead in the sheet.
- Зависит от FEAT-002 для данных (`CrmLead` cache + sync).

## User Flow

- FLOW-001

## Related Systems

- PAGE-002, PAGE-003
- FEAT-002, FEAT-004 (переход к разбору)

## Implementation Links

- Roadmap: STAGE-003 (done) — [roadmap-manager-dashboard.md](../../project/roadmap-manager-dashboard.md)
- Backend: `apps/api/analytics/`
- Frontend: `apps/web/src/app/manager/`, `components/ManagerDashboard.tsx`, `ClientsToReview.tsx`

## Security Impact

- Данные только в scope руководителя.

## Acceptance Criteria

QA-AC-001, QA-AC-002, QA-AC-003, QA-AC-004

## Test Notes

- Проверить все периоды и drill-down.
- Проверить AI-сводку с данными и без.

## Release Notes

PAGE-002 + PAGE-003 shipped 2026-06-09.
