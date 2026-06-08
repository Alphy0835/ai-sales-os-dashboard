Doc ID: FEAT-005
Status: draft
Related requirements: REQ-007, REQ-008
Related user flows: FLOW-003, FLOW-004
Related API: TBD — `docs/architecture/api-contracts.md`
Related data model: TBD — `docs/architecture/data-model.md`
Related security: `docs/security/data-classification.md`
Related tests: QA-AC-007, QA-AC-008
Update trigger: изменение критериев оценки, шаблонов отчётов или формата канваса
Owner: product
Review required: product, backend, AI

# Quality & AI Analytics

## Purpose

Оценивать качество общения по транскрипциям и давать руководителю AI-отчёты с канвасами и рекомендациями.

## Description

- Настройка критериев оценки на PAGE-006 (REQ-008).
- AI-аналитика (PAGE-005): стандартные шаблоны отчётов (REQ-007).
- Канвасы: качество на этапах, динамика, рекомендации к разбору.
- Запуск по сотруднику или подразделению; права view / run.
- Зависит от FEAT-002 (транскрипции) и настроенных критериев.

## User Flow

- FLOW-003, FLOW-004 (критерии)

## Related Systems

- PAGE-005, PAGE-006 (критерии)
- FEAT-002, FEAT-004 (рекомендации → разбор)

## Implementation Links

- Roadmap: STAGE-005

## Security Impact

- Транскрипции и записи — чувствительные данные.

## Acceptance Criteria

QA-AC-007, QA-AC-008

## Test Notes

- Отчёт без транскрипций → понятная ошибка.
- Изменение критерия → отражается в новом отчёте.

## Release Notes

TBD
