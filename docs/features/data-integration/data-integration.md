Doc ID: FEAT-002
Status: draft
Related requirements: REQ-015, REQ-016, REQ-NFR-002, REQ-NFR-003
Related user flows: FLOW-001, FLOW-003, FLOW-006
Related API: TBD — `docs/architecture/api-contracts.md`
Related data model: TBD — `docs/architecture/data-model.md`
Related security: `docs/security/secrets-management.md`, `docs/architecture/integrations.md`
Related tests: QA-AC-015, QA-AC-016, QA-AC-NFR-002, QA-AC-NFR-003
Update trigger: добавление источника данных, изменение правил агрегации или транскрипции
Owner: backend
Review required: backend, security

# Data Integration

## Purpose

Подтянуть операционные показатели и записи общений из внешних систем для дашбордов и AI-аналитики.

## Description

- Источники: CRM, телефония, встроенная/сторонняя отчётность.
- Агрегация метрик для дашбордов руководителя и сотрудника.
- Приём аудио/видео из телефонии и ручной загрузки.
- Транскрипция записей для AI-оценки качества.
- Явные состояния при недоступности или частичной недоступности источника.

## User Flow

- FLOW-001, FLOW-003, FLOW-006 (потребление данных)

## Related Systems

- `docs/architecture/integrations.md`
- FEAT-003, FEAT-005 (потребители данных)

## Implementation Links

- Roadmap: STAGE-002

## Security Impact

- Хранение и доступ к записям общений и транскрипциям.
- Секреты интеграций — `docs/security/secrets-management.md`.

## Acceptance Criteria

QA-AC-015, QA-AC-016, QA-AC-NFR-002, QA-AC-NFR-003

## Test Notes

- Симулировать недоступность CRM и телефонии по отдельности.
- Проверить актуальность блока «сегодня».

## Release Notes

TBD
