Doc ID: FEAT-006
Status: draft
Related requirements: REQ-010, REQ-011, REQ-012
Related user flows: FLOW-004, FLOW-005, FLOW-007
Related API: TBD — `docs/architecture/api-contracts.md`
Related data model: TBD — `docs/architecture/data-model.md`
Related security: FEAT-001 (доступ к материалам RAG)
Related tests: QA-AC-010, QA-AC-011, QA-AC-012
Update trigger: изменение базы знаний, поведения AI-агентов или прав на материалы
Owner: product
Review required: product, AI, security

# Knowledge Base & AI Agents

## Purpose

Накопить знания компании и дать руководителю и сотруднику AI-помощников с RAG-контекстом.

## Description

- База знаний (PAGE-006): продукты, отработки, infопovоды, кейсы (REQ-010).
- AI-агент руководителя (PAGE-007): стратегия, скрипты, контекст клиента (REQ-011).
- AI-агент сотрудника (PAGE-009): отработки, продукт, клиент (REQ-012).
- RAG с учётом прав и scope; обучение на успешных/неуспешных сделках.
- Контекст: комментарий о клиенте, аудио/видео записи.

## User Flow

- FLOW-004, FLOW-005, FLOW-007

## Related Systems

- PAGE-006, PAGE-007, PAGE-009
- FEAT-001, FEAT-002

## Implementation Links

- Roadmap: STAGE-006

## Security Impact

- Материалы RAG фильтруются по правам пользователя.
- Агент сообщает об ограничении контекста (REQ-NFR-004).

## Acceptance Criteria

QA-AC-010, QA-AC-011, QA-AC-012

## Test Notes

- Добавить материал → проверить ответ агента.
- Запрос вне прав → явное сообщение.

## Release Notes

TBD
