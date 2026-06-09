Doc ID: FEAT-001
Status: in progress
Related requirements: REQ-013, REQ-014, REQ-NFR-001, REQ-NFR-004
Related user flows: FLOW-004
Related API: API-AUTH-001 … API-AUTH-004 — `docs/architecture/api-contracts.md`
Related data model: Tenant, Workspace, User, ModulePermission — `docs/architecture/data-model.md`
Related security: `docs/security/auth-and-access-control.md`, `docs/security/audit-logging.md`
Related tests: QA-AC-013, QA-AC-014, QA-AC-NFR-001, QA-AC-NFR-004
Update trigger: изменение ролей, прав, иерархии или правил делегирования
Owner: product
Review required: product, security

# Access & Permissions

## Purpose

Обеспечить вход в User Level, иерархию руководителей, granular permissions и изоляцию данных по scope.

## Description

- Авторизация пользователей User Level (руководитель, сотрудник).
- Многоуровневая иерархия руководителей с разным scope подразделений.
- Модули прав: dashboard, clients, reviews, analytics, settings, agent.
- Режимы: none / view / edit / run / use.
- Правило потолка: нельзя выдать право шире, чем у назначающего.
- Управление доступами сотрудников — подраздел «Права» на PAGE-006.

## User Flow

- FLOW-004 (настройка прав)
- `docs/project/user-roles.md`

## Related Systems

- `docs/security/auth-and-access-control.md`
- PAGE-001, PAGE-006

## Implementation Links

- Roadmap: STAGE-001 (in progress)
- Code: `apps/api/accounts/`, `apps/web/src/app/login/`, `apps/web/src/components/ProtectedShell.tsx`
- Pages: PAGE-001 (implemented), PAGE-006 (права — planned)

## Security Impact

- Изоляция данных по scope (REQ-NFR-001).
- Аудит изменений прав (REQ-NFR-001).
- Блокировка эскалации прав (REQ-014).

## Acceptance Criteria

QA-AC-013, QA-AC-014, QA-AC-NFR-001, QA-AC-NFR-004

## Test Notes

- Проверить двухуровневую иерархию руководителей.
- Проверить все режимы прав на каждый модуль.

## Release Notes

TBD
