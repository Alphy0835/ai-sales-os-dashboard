Doc ID: FEAT-007
Status: done
Related requirements: REQ-009
Related user flows: FLOW-004, FLOW-003
Related API: `docs/architecture/api-contracts.md` — API-CR-001
Related data model: `docs/architecture/data-model.md` — CustomReport
Related security: FEAT-001
Related tests: QA-AC-009
Update trigger: изменение формата кастомных отчётов или правил структурирования промптов
Owner: product
Review required: product, AI

# Custom AI Reports

## Purpose

Позволить руководителю описывать кастомные отчёты простым языком и повторно их запускать.

## Description

- Описание желаемого отчёта на PAGE-006 (REQ-009).
- Система структурирует описание в AI-запрос.
- Сохранение и повторный запуск из PAGE-005 (AI-аналитика).
- STAGE-007 complete (2026-06-09).

## User Flow

- FLOW-004 (создание), FLOW-003 (запуск)

## Related Systems

- PAGE-005, PAGE-006
- FEAT-005

## Implementation Links

- Roadmap: STAGE-007 (done) — [roadmap-custom-ai-reports.md](../../project/roadmap-custom-ai-reports.md)
- Code: `apps/api/ai/services/custom_reports.py`, `apps/web/src/app/manager/settings/` (`CustomReportsSettings.tsx`), `AiAnalytics.tsx`

## Security Impact

- Доступ к созданию — по правам settings: edit.

## Acceptance Criteria

QA-AC-009

## Test Notes

- Создать отчёт → сохранить → запустить повторно.

## Release Notes

TBD
