Doc ID: SECURITY-AUTH-001
Status: active
Source of truth: yes
Owner: security
Related docs: docs/architecture/api-contracts.md, docs/architecture/data-model.md, docs/project/user-roles.md, docs/features/access-permissions/access-permissions.md, docs/backend/backend-docs.md
Update together with: api-contracts.md, data-model.md, user-roles.md, FEAT-001
Update trigger: изменение auth flow, JWT, roles, permissions, tenant isolation
Review required: security, backend
Maturity: L2

# Auth and Access Control

Техническая реализация User Level auth (STAGE-001, in progress). Продуктовые правила — `docs/project/user-roles.md`.

> API контракты: [api-contracts.md](../architecture/api-contracts.md) · Модель данных: [data-model.md](../architecture/data-model.md)

## User Level Authentication

| Aspect | Implementation (MVP) |
|---|---|
| Protocol | JWT access + refresh (SimpleJWT) |
| Login | `POST /api/v1/auth/login/` — email + password |
| Session storage (client) | `localStorage` access/refresh (Next.js) |
| Token claims | `tenant_id`, `role` in JWT payload |
| Me / context | `GET /api/v1/auth/me/` — user, workspace, module permissions |

## Roles (User Level)

| Role | Code | Shell | Home route |
|---|---|---|---|
| Руководитель | `manager` | SHELL-MANAGER | `/manager` |
| Сотрудник | `employee` | SHELL-EMPLOYEE | `/employee` |

Integration Level (интегратор) — Django Admin, session auth; отдельный flow, позже.

## Module Permissions

Granular access per module (`ModulePermission`):

| Module | Levels |
|---|---|
| dashboard, clients, reviews, analytics, settings, agent | `none` · `view` · `edit` · `run` · `use` |

Returned in `/auth/me/` as `permissions` object. UI gating — frontend; enforcement — backend on each endpoint (STAGE-001+).

## Multi-tenant Isolation

- Every tenant-scoped row has `tenant_id`.
- `TenantMiddleware` attaches `request.tenant` from authenticated user.
- Querysets MUST filter by user's tenant (see `apps/api/core`).

## Ceiling Rule (REQ-014)

**Product rule:** grantor cannot assign permission broader than their own.

**Status:** specified in PRD/user-roles; **API for grant/revoke not implemented yet** (PAGE-006 settings).

## Not Yet Implemented

- Manager hierarchy (multi-level scope)
- Permission grant/revoke API
- Audit log on permission changes
- Refresh token blacklist / server-side logout
- Rate limiting on login

## Related Docs

- [FEAT-001](../features/access-permissions/access-permissions.md)
- [backend-docs.md](../backend/backend-docs.md) — Django apps
- [frontend-docs.md](../frontend/frontend-docs.md) — auth states, ProtectedShell
