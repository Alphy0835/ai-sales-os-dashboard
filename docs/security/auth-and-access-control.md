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

Техническая реализация User Level auth (STAGE-001, done). Продуктовые правила — `docs/project/user-roles.md`.

> API контракты: [api-contracts.md](../architecture/api-contracts.md) · Модель данных: [data-model.md](../architecture/data-model.md)

## User Level Authentication

| Aspect | Implementation (MVP) |
|---|---|
| Protocol | JWT access + refresh (SimpleJWT) |
| Login | `POST /api/v1/auth/login/` — email + password |
| Session storage (client) | **httpOnly cookies** (`access_token`, `refresh_token`) set by API; browser calls same-origin `/api/v1/*` via Next.js BFF rewrites (`next.config.ts` → `API_BACKEND_URL`) |
| Token transport | `credentials: "include"` on all auth/API fetches; `CookieJWTAuthentication` reads access cookie; `Authorization: Bearer` fallback for tests and API clients |
| Display cache | `localStorage` stores non-secret user profile (`ai_sales_os_user`) for fast shell render — **not** JWT tokens |
| Token claims | `tenant_id`, `role` in JWT payload |
| Me / context | `GET /api/v1/auth/me/` — user, workspace, module permissions, scope workspaces |
| Refresh | `POST /api/v1/auth/refresh/` — refresh from httpOnly cookie (`CookieTokenRefreshSerializer`); rotates refresh token; `BLACKLIST_AFTER_ROTATION` |
| Logout | `POST /api/v1/auth/logout/` — blacklists refresh token (`token_blacklist`), clears auth cookies |

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

Returned in `/auth/me/` as `permissions` object. Grant via `PUT /api/v1/permissions/users/{id}/` (requires `settings: edit`).

## Manager Hierarchy & Scope

- `User.manager` — parent manager (multi-level hierarchy).
- `ManagerScope` — workspaces a manager can access.
- Sub-manager workspace scope must be subset of parent scope.
- Employees visible to manager if `employee.workspace` ∈ manager scoped workspaces.
- Scope API: `GET /api/v1/scope/`, check: `GET /api/v1/scope/users/{id}/` (403 + audit on violation).

Implementation: `apps/api/accounts/services/scope.py`.

## Multi-tenant Isolation

- Every tenant-scoped row has `tenant_id`.
- Querysets MUST filter by authenticated `user.tenant_id` in views/services — not via custom ORM managers.
- `TenantMiddleware` attaches `request.tenant` from the user for downstream convenience; isolation is enforced in view/queryset code (see [data-model.md](../architecture/data-model.md)).

## Ceiling Rule (REQ-014)

Grantor cannot assign permission broader than their own per module. Enforced in `accounts/services/grant.py`. Violations → HTTP 400.

## Audit

Permission changes and scope-denied attempts logged to `AuditLog`. See [audit-logging.md](audit-logging.md).

## Rate Limiting

| Endpoint | Throttle | Env | Implementation |
|---|---|---|---|
| `POST /auth/login/`, refresh | 10/min | `THROTTLE_LOGIN` | `LoginRateThrottle` in `accounts/views.py` |
| Agent chat endpoints | 30/min | `THROTTLE_AGENT` | `AgentRateThrottle` in `ai/views.py` |

Disabled when `TESTING=true`. See [security-checklist.md](security-checklist.md).

## Knowledge Grants (PAGE-006)

Per-user KB access overrides via `KnowledgeArticleGrant`. UI: PAGE-006 Access tab (modules, audit log, knowledge grants). API: `GET/PUT /api/v1/permissions/users/{id}/knowledge/` (API-PERM-004).

## Cookie Auth Flow (BFF)

1. Browser `POST /api/v1/auth/login/` → Next rewrites to Django → response sets httpOnly `access_token` + `refresh_token` (`accounts/cookies.py`).
2. Subsequent API calls use `credentials: "include"`; Django authenticates via `CookieJWTAuthentication`.
3. On `401`, client calls `POST /api/v1/auth/refresh/` with refresh cookie only (`apps/web/src/lib/api.ts`).
4. Logout blacklists refresh and clears cookies (`accounts/views.py` `LogoutView`).

Production: `NEXT_PUBLIC_API_URL` must be empty so the browser stays same-origin. See [deployment.md](../operations/deployment.md).

## Related Docs

- [FEAT-001](../features/access-permissions/access-permissions.md)
- [roadmap-access-permissions.md](../project/roadmap-access-permissions.md)
- [backend-docs.md](../backend/backend-docs.md) — Django apps
- [frontend-docs.md](../frontend/frontend-docs.md) — auth states, ProtectedShell
