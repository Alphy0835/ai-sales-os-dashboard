Doc ID: FEAT-007
Status: draft
Related requirements: REQ-009
Related user flows: FLOW-004, FLOW-003
Related API: TBD — `docs/architecture/api-contracts.md`
Related data model: TBD — `docs/architecture/data-model.md`
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
- Post-MVP; не блокирует первый релиз User Level.

## User Flow

- FLOW-004 (создание), FLOW-003 (запуск)

## Related Systems

- PAGE-005, PAGE-006
- FEAT-005

## Implementation Links

- Roadmap: STAGE-007

## Security Impact

- Доступ к созданию — по правам settings: edit.

## Acceptance Criteria

QA-AC-009

## Test Notes

- Создать отчёт → сохранить → запустить повторно.

## Release Notes

TBD
