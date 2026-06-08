Doc ID:
Status: draft / active / deprecated
Source of truth: yes / no
Owner:
Related docs:
Update together with:
Update trigger:
Review required:
Maturity:

<!-- backend-docs.md — общий индекс backend-структуры проекта. Файл описывает модули, сервисы, API handlers, работу с данными, интеграции, фоновые задачи, ошибки, логи и связи с architecture/security/operations. Не дублируем детальные API и data model, а ссылаемся на api-contracts.md и data-model.md. -->

# Backend Docs

## Purpose

<!-- Кратко: за что отвечает backend в продукте, какие бизнес-процессы обслуживает, какие границы ответственности имеет. -->

## Backend Scope

| Area | Included | Notes | Related Docs |
|---|---|---|---|
| API | yes / no | REST / GraphQL / RPC / webhooks | docs/architecture/api-contracts.md |
| Auth | yes / no | login, sessions, roles, permissions | docs/security/auth-and-access-control.md |
| Data access | yes / no | database, repositories, ORM | docs/architecture/data-model.md |
| Integrations | yes / no | payments, email, AI API, CRM, storage | docs/architecture/integrations.md |
| Background jobs | yes / no | queues, cron, async workers |  |
| Admin actions | yes / no | internal tools, moderation, support actions | docs/security/audit-logging.md |

## Modules / Services

| Module / Service | Responsibility | Main Data | Related API | Related Features |
|---|---|---|---|---|
|  |  |  | API-... | FEAT-... |

## API Handlers

<!-- Не описывать все контракты заново. Здесь только карта backend handlers и ссылки на api-contracts.md. -->

| Handler / Route Group | Purpose | Auth Required | Related API Contract |
|---|---|---|---|
|  |  | yes / no | API-... |

## Data Access

<!-- Как backend работает с данными: repositories, ORM, migrations, transactions, validation. Детали сущностей в data-model.md. -->

| Data Area | Storage | Access Pattern | Related Data Model |
|---|---|---|---|
|  |  |  |  |

## Validation Rules

<!-- Где валидируются входные данные, какие ошибки возвращаются, что проверяется на backend независимо от frontend. -->

## Auth / Permissions

<!-- Кратко: какие backend-зоны требуют авторизации, где проверяются роли/permissions. Детали в auth-and-access-control.md. -->

## Background Jobs

| Job | Trigger | Purpose | Failure Handling | Related Docs |
|---|---|---|---|---|
|  | cron / event / manual |  | retry / alert / dead-letter |  |

## Integrations

<!-- Краткая карта интеграций backend. Детали ключей, лимитов и webhooks — в integrations.md и secrets-management.md. -->

| Integration | Used For | Failure Behavior | Related Docs |
|---|---|---|---|
|  |  |  | docs/architecture/integrations.md |

## Error Handling

<!-- Общие правила ошибок: какие ошибки показываем клиенту, какие логируем, какие превращаются в alerts. -->

## Logging / Observability

<!-- Какие события логируются, какие метрики важны, что нельзя логировать. -->

## Migrations

<!-- Как создаются, запускаются и откатываются миграции. Ссылки на deployment.md и rollback.md. -->

## Security Notes

<!-- Backend-specific security: input validation, auth checks, rate limits, secrets, audit events. -->

## Related Docs

- docs/architecture/system-overview.md
- docs/architecture/api-contracts.md
- docs/architecture/data-model.md
- docs/architecture/integrations.md
- docs/security/auth-and-access-control.md
- docs/security/secrets-management.md
- docs/security/audit-logging.md
- docs/operations/deployment.md
- docs/operations/rollback.md

<!-- Файл может содержать в себе не все элементы описанные сейчас, а так же может иметь и дополнения и расширения в зафисимости от специфики проекта -->