Doc ID: FEAT-002
Status: done
Related requirements: REQ-015, REQ-016, REQ-NFR-002, REQ-NFR-003
Related user flows: FLOW-001, FLOW-003, FLOW-006
Related API: API-INT-001 … API-INT-007 — `docs/architecture/api-contracts.md`
Related data model: IntegrationSource, MetricSnapshot, ConversationRecording, Transcription — `docs/architecture/data-model.md`
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
- **CRM (P4c):** Google Sheets → `CrmLead` **DB cache**; sync hourly background + on-demand (login throttled, manual API, agent refresh) — **not** 24/7 realtime.
- User Level и manager-agent читают PostgreSQL, не live Sheets и не batch LLM по всем комментариям CRM.
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

- Roadmap: STAGE-002 (done) — [roadmap-data-integration.md](../../project/roadmap-data-integration.md)
- Code: `apps/api/integrations/`
- Seed: `python manage.py seed_integrations`

## Security Impact

- Хранение и доступ к записям общений и транскрипциям.
- Секреты интеграций — `docs/security/secrets-management.md`.

## Acceptance Criteria

QA-AC-015, QA-AC-016, QA-AC-NFR-002, QA-AC-NFR-003

## Test Notes

- Симулировать недоступность CRM и телефонии по отдельности.
- Проверить актуальность блока «сегодня».

## Release Notes

Backend API + demo adapters shipped 2026-06-09.
