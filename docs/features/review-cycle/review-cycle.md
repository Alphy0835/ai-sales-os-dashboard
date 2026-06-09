Doc ID: FEAT-004
Status: active
Related requirements: REQ-005, REQ-006
Related user flows: FLOW-002, FLOW-006
Related API: `docs/architecture/api-contracts.md` — API-REV-001, API-REV-002
Related data model: `docs/architecture/data-model.md` — Review, ReviewTask
Related security: FEAT-001 (scope), `docs/security/audit-logging.md`
Related tests: QA-AC-005, QA-AC-006
Update trigger: изменение модели разбора, задач или личного дашборда сотрудника
Owner: product
Review required: product, frontend

# Review Cycle

## Purpose

Замкнуть цикл контроля: разбор → задачи → выполнение → фиксация результата.

## Description

- История разборов (PAGE-004): сотрудник, дата, комментарий, обсуждение, задачи.
- Фильтры по подразделению и сотруднику.
- Права view / edit на модуль reviews.
- Задачи из разбора отображаются на личном дашборде сотрудника (PAGE-008).
- Статус выполнения задач обновляется в истории разборов.

## User Flow

- FLOW-002, FLOW-006

## Related Systems

- PAGE-004, PAGE-008
- FEAT-003 (вход из клиентов к разбору / дашборда)

## Implementation Links

- Roadmap: STAGE-004

## Security Impact

- Сотрудник видит только свои задачи и показатели.
- Создание разборов — audit event.

## Acceptance Criteria

QA-AC-005, QA-AC-006

## Test Notes

- End-to-end: разбор → задача на дашборде сотрудника → обновление статуса.

## Release Notes

TBD
