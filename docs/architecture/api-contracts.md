Doc ID: ARCH-API-001
Status: active
Source of truth: yes
Owner: backend
Related docs: docs/architecture/data-model.md, docs/backend/backend-docs.md, docs/frontend/frontend-docs.md, docs/features/access-permissions/access-permissions.md
Update together with: data-model.md, backend-docs.md, frontend-docs.md
Update trigger: новый endpoint, изменение request/response или auth
Review required: backend, frontend
Maturity: L2

# API Contracts

Base path: `/api/v1/`  
Format: JSON  
Auth default: httpOnly `access_token` cookie (BFF same-origin); `Authorization: Bearer` supported for tests and API clients  
OpenAPI: `/api/schema/` (drf-spectacular)

> STAGE-001–007 implemented. Browser calls same-origin `/api/v1/*`; Next.js rewrites to Django (`API_BACKEND_URL`). Production: `NEXT_PUBLIC_API_URL=""`.

## Cookie Auth (BFF)

| Step | Endpoint | Cookies | Client behavior |
|---|---|---|---|
| Login | `POST /auth/login/` | Sets `access_token`, `refresh_token` (httpOnly, Secure in prod, SameSite=Lax) | `credentials: "include"`; optional `user` in JSON body |
| API calls | any authenticated path | Sends `access_token` | `authFetch` with `credentials: "include"` |
| Refresh | `POST /auth/refresh/` | Reads `refresh_token`; sets new pair | Cookie-only body optional; rotates refresh |
| Logout | `POST /auth/logout/` | Blacklists refresh; clears both cookies | `credentials: "include"` |

Implementation: `accounts/cookies.py`, `accounts/authentication.py` (`CookieJWTAuthentication`), `accounts/serializers_auth.py`, `apps/web/next.config.ts` rewrites.

## API Index

| API ID | Method | Path | Purpose | Auth | Feature |
|---|---|---|---|---|---|
| API-HEALTH-001 | GET | `/health/` | Liveness | no | — |
| API-HEALTH-002 | GET | `/health/ready/` | Readiness (DB, Redis, Celery) | no | — |
| API-AUTH-001 | POST | `/auth/login/` | Login, issue JWT | no | FEAT-001 |
| API-AUTH-002 | POST | `/auth/refresh/` | Refresh access token | refresh cookie (body fallback) | FEAT-001 |
| API-AUTH-003 | GET | `/auth/me/` | Current user + permissions + scope | yes | FEAT-001 |
| API-AUTH-004 | POST | `/auth/logout/` | Blacklist refresh + clear cookies | refresh cookie (body fallback) | FEAT-001 |
| API-AUTH-005 | POST | `/auth/register/` | Register via invite token (P4b-GS) | no | FEAT-001 |
| API-SCOPE-001 | GET | `/scope/` | Workspaces and users in scope | yes | FEAT-001 |
| API-SCOPE-002 | GET | `/scope/users/{id}/` | Check user access in scope | yes | FEAT-001 |
| API-PERM-001 | GET | `/permissions/users/` | List users in scope + permissions | yes (settings view/edit) | FEAT-001 |
| API-PERM-002 | GET | `/permissions/users/{id}/` | User permissions detail | yes (settings view/edit) | FEAT-001 |
| API-PERM-003 | PUT | `/permissions/users/{id}/` | Grant permissions (ceiling rule) | yes (settings edit) | FEAT-001 |
| API-PERM-004 | GET/PUT | `/permissions/users/{id}/knowledge/` | Per-user KB article grants | yes (settings view/edit) | FEAT-001 |
| API-AUDIT-001 | GET | `/audit/permissions/` | Permission change audit log | yes (settings view/edit) | FEAT-001 |
| API-INT-001 | GET | `/integrations/sources/` | Integration sources + health | yes (dashboard view) | FEAT-002 |
| API-INT-002 | GET | `/integrations/metrics/` | Aggregated metrics + completeness | yes (dashboard view) | FEAT-002 |
| API-INT-003 | GET | `/integrations/recordings/` | Recordings in scope | yes (dashboard view) | FEAT-002 |
| API-INT-004 | POST | `/integrations/recordings/` | Manual recording upload | yes (dashboard view) | FEAT-002 |
| API-INT-005 | GET | `/integrations/recordings/{id}/` | Recording detail | yes (dashboard view) | FEAT-002 |
| API-INT-006 | GET | `/integrations/recordings/{id}/transcription/` | Transcription text | yes (dashboard view) | FEAT-002 |
| API-INT-007 | POST | `/integrations/recordings/{id}/transcription/` | Queue (re)transcription | yes (dashboard view) | FEAT-002 |
| API-INT-008 | POST | `/integrations/sources/{id}/sync/` | Queue manual CRM/sync | yes (settings edit) | FEAT-002 |
| API-MGR-001 | GET | `/manager/dashboard/` | Manager dashboard aggregate | yes (manager, dashboard view) | FEAT-003 |
| API-MGR-002 | GET | `/manager/clients/` | Clients to review | yes (manager, `clients: view` OR `dashboard: view`) | FEAT-003 |
| API-EMP-001 | GET | `/employee/dashboard/` | Employee personal metrics | yes (employee, dashboard view) | FEAT-003 |
| API-REV-001 | GET/POST | `/manager/reviews/` | Review list + create | yes (manager, reviews) | FEAT-004 |
| API-REV-002 | PATCH | `/employee/tasks/{id}/` | Employee task status update | yes (employee) | FEAT-004 |
| API-AI-001 | GET/POST/PATCH/DELETE | `/manager/settings/quality-criteria/` | Quality criteria CRUD | yes (settings) | FEAT-005 |
| API-AI-002 | GET | `/manager/analytics/reports/` | Analytics reports list | yes (analytics view/run) | FEAT-005 |
| API-AI-003 | POST | `/manager/analytics/reports/run/` | Run analytics report | yes (analytics run) | FEAT-005 |
| API-CR-001 | GET/POST/PATCH/DELETE | `/manager/settings/custom-reports/` | Custom AI reports CRUD | yes (settings) | FEAT-007 |
| API-KB-001 | GET/POST/PATCH/DELETE | `/manager/settings/knowledge/` | Knowledge base CRUD | yes (settings) | FEAT-006 |
| API-AGENT-001 | POST | `/manager/agent/chat/`, `/employee/agent/chat/` | AI agent chat | yes (agent use) | FEAT-006 |

---

## API-HEALTH-001 — Liveness

Public. Does not check dependencies — use for process-alive probes only.

### Response `200`

```json
{ "status": "ok", "service": "ai-sales-os-api" }
```

---

## API-HEALTH-002 — Readiness

Public. Verifies database, Redis broker (`CELERY_BROKER_URL`), and Celery worker availability (`inspect().ping()`).

### Response `200` — all checks pass

```json
{
  "status": "ok",
  "service": "ai-sales-os-api",
  "checks": {
    "database": { "status": "ok" },
    "redis": { "status": "ok" },
    "celery": { "status": "ok" }
  }
}
```

### Response `503` — one or more checks failed

```json
{
  "status": "error",
  "service": "ai-sales-os-api",
  "checks": {
    "database": { "status": "ok" },
    "redis": { "status": "ok" },
    "celery": { "status": "error", "error": "no workers responded" }
  }
}
```

Failed checks include an `error` string. Production Docker healthcheck targets this endpoint.

---

## API-AUTH-001 — Login

### Purpose

Authenticate User Level user; set httpOnly auth cookies and return user + role for frontend routing.

### Authorization

Public.

### Cookies set on `200`

`access_token`, `refresh_token` (httpOnly, Secure in production, SameSite=Lax, path `/`).

### Request

```json
{
  "email": "manager@demo.local",
  "password": "demo1234"
}
```

### Response `200`

```json
{
  "access": "<jwt_access>",
  "refresh": "<jwt_refresh>",
  "user": {
    "id": "uuid",
    "email": "manager@demo.local",
    "full_name": "Demo Manager",
    "role": "manager",
    "tenant_id": "uuid",
    "workspace_id": "uuid",
    "workspace_name": "ОП Москва"
  }
}
```

`role`: `manager` | `employee` — maps to SHELL-MANAGER / SHELL-EMPLOYEE routes.

JSON `access` / `refresh` fields may be present for API clients; **browser clients use httpOnly cookies** and should not persist tokens in JS storage.

### Behavior (P4b-GS)

On `200`, queues async CRM sync for the user's tenant (Google Sheets → `CrmLead` cache). Response unchanged; sync is non-blocking.

### Errors

| Code | Meaning | Client behavior |
|---|---|---|
| 400 | Validation error | Show field errors |
| 401 | Invalid credentials | Show login error |

---

## API-AUTH-005 — Register (invite)

### Purpose

Create User Level account from `RegistrationInvite` (Google Sheets onboarding). Public endpoint; invite token proves eligibility.

### Authorization

Public. Requires valid `token` query param or body field matching unused, unexpired `RegistrationInvite`.

### Request

```json
{
  "token": "<invite_token>",
  "password": "secure-password-min-8",
  "full_name": "Иван Иванов"
}
```

`email` is taken from the invite record (not client-supplied). Optional `full_name` overrides display name; default from invite metadata or email local-part.

### Response `201`

```json
{
  "user": {
    "id": "uuid",
    "email": "employee@demo.local",
    "full_name": "Иван Иванов",
    "role": "employee",
    "tenant_id": "uuid",
    "workspace_id": "uuid"
  }
}
```

Does **not** set auth cookies — client redirects to login. After first `POST /auth/login/`, CRM sync links `CrmLead` rows by `employee_email`.

### Errors

| Code | Meaning | Client behavior |
|---|---|---|
| 400 | Weak password, validation | Show field errors |
| 404 | Unknown token | Invalid invite link |
| 410 | Expired or already used invite | Ask manager for new invite |

Invite creation: Django Admin only (MVP). See [integrations.md](integrations.md) RegistrationInvite flow.

---

## API-AUTH-002 — Refresh

### Request

Primary: httpOnly `refresh_token` cookie (no body required).

Optional body fallback (tests, non-browser clients):

```json
{ "refresh": "<jwt_refresh>" }
```

### Response `200`

Sets new `access_token` and `refresh_token` cookies. JSON body may include:

```json
{
  "access": "<new_jwt_access>",
  "refresh": "<new_jwt_refresh>"
}
```

Refresh rotation enabled (`ROTATE_REFRESH_TOKENS`, `BLACKLIST_AFTER_ROTATION`).

### Errors

| Code | Meaning |
|---|---|
| 401 | Invalid/expired/blacklisted refresh |

---

## API-AUTH-003 — Me

### Purpose

Load shell context: user, workspace, module permissions for UI gating.

### Response `200`

```json
{
  "id": "uuid",
  "email": "manager@demo.local",
  "full_name": "Demo Manager",
  "role": "manager",
  "tenant_id": "uuid",
  "workspace": {
    "id": "uuid",
    "name": "ОП Москва"
  },
  "permissions": {
    "dashboard": "view",
    "clients": "view",
    "reviews": "edit",
    "analytics": "run",
    "settings": "edit",
    "agent": "use"
  },
  "scope": {
    "workspaces": [{ "id": "uuid", "name": "ОП Москва" }]
  }
}
```

Module keys match [user-roles.md](../project/user-roles.md). Values: `none` | `view` | `edit` | `run` | `use`.

### Errors

| Code | Meaning | Client behavior |
|---|---|---|
| 401 | Missing/invalid token | Redirect to `/login` |
| 403 | User inactive | Show forbidden |

---

## API-AUTH-004 — Logout

### Purpose

Invalidate refresh token server-side and clear auth cookies.

### Authorization

Public (uses refresh cookie or optional body `refresh`).

### Behavior

1. Blacklist refresh token via `rest_framework_simplejwt.token_blacklist`.
2. Clear `access_token` and `refresh_token` cookies.

### Response `204`

No body. Subsequent refresh with the same token → `401`.

---

## API-SCOPE-001 — Scope

### Purpose

Return workspaces and users visible to the authenticated user (hierarchy + workspace scope).

### Response `200`

```json
{
  "workspaces": [{ "id": "uuid", "name": "ОП Москва" }],
  "users": [
    {
      "id": "uuid",
      "email": "employee@demo.local",
      "full_name": "Demo Employee",
      "role": "employee",
      "workspace": { "id": "uuid", "name": "ОП Москва" },
      "manager_id": null
    }
  ]
}
```

---

## API-SCOPE-002 — Scope user access check

### Purpose

Verify target user is within actor scope; log `scope_denied` audit on 403.

### Response `200`

```json
{
  "accessible": true,
  "user": { "id": "uuid", "email": "...", "role": "employee", "workspace": { "id": "uuid", "name": "..." }, "manager_id": null },
  "permissions": { "dashboard": "view", "agent": "use" }
}
```

### Errors

| Code | Meaning |
|---|---|
| 403 | User outside scope |
| 404 | User not found in tenant |

---

## API-PERM-001 — List users for permission management

### Response `200`

Array of users in scope with `permissions` object (same shape as `/auth/me/`).

---

## API-PERM-003 — Grant permissions

### Authorization

Requires `settings: edit`. Enforces **ceiling rule** (REQ-014): grantor cannot assign level broader than their own per module.

### Request

```json
{
  "permissions": {
    "reviews": "view",
    "agent": "use"
  }
}
```

### Response `200`

User object with updated `permissions`.

### Errors

| Code | Meaning |
|---|---|
| 400 | Invalid module/level or ceiling violation |
| 403 | Target outside scope or missing settings edit |

---

## API-PERM-004 — Knowledge article grants

Requires `settings: view` (GET) or `settings: edit` (PUT). Target user must be in grantor scope.

### GET `/permissions/users/{id}/knowledge/` — Response `200`

```json
{
  "grants": [
    {
      "article_id": "uuid",
      "title": "Playbook",
      "access_level": "manager",
      "base_accessible": false,
      "is_allowed": true,
      "grantor_can_assign": true
    }
  ]
}
```

### PUT `/permissions/users/{id}/knowledge/` — Body

```json
{
  "grants": [
    { "article_id": "uuid", "is_allowed": true }
  ]
}
```

**Ceiling:** grantor cannot assign access to articles they cannot access themselves.

| Code | Meaning |
|---|---|
| 400 | Ceiling violation or invalid article |
| 403 | Target outside scope or missing settings edit |

---

## API-AUDIT-001 — Permission audit log

### Query params

| Param | Description |
|---|---|
| `user_id` | Filter by target user (optional) |
| `action` | Filter by audit action (optional). Comma-separated values: `permission_change`, `review_create`, `scope_denied`. Default when omitted: `permission_change` only |
| `limit` | Max rows, default 50, max 200 |

### Response `200`

```json
{
  "results": [
    {
      "id": "uuid",
      "action": "permission_change",
      "module": "reviews",
      "old_level": "none",
      "new_level": "view",
      "actor": { "id": "uuid", "email": "regional@demo.local", "full_name": "..." },
      "target_user": { "id": "uuid", "email": "employee@demo.local", "full_name": "..." },
      "created_at": "2026-06-09T12:00:00Z"
    }
  ]
}
```

---

## API-INT-002 — Metrics summary

### Query params

| Param | Values | Description |
|---|---|---|
| `period` | `today` (default), `week`, `month` | Aggregation window |
| `workspace_id` | UUID | Filter by workspace (manager scope) |
| `user_id` | UUID | Filter by employee |

### Response `200`

```json
{
  "period": "today",
  "as_of": "2026-06-09T12:00:00Z",
  "completeness": "partial",
  "completeness_reason": "частично: telephony",
  "sources": [
    { "source_type": "crm", "status": "connected", "last_sync_at": "..." },
    { "source_type": "telephony", "status": "degraded", "last_error": null }
  ],
  "metrics": {
    "calls": { "label": "Звонки", "value": 8.0, "available": true, "sources": ["telephony"], "reason": null },
    "quality_score": { "label": "Оценка качества", "value": null, "available": false, "reason": "telephony_degraded" }
  }
}
```

`completeness`: `full` | `partial` | `empty` — REQ-NFR-003.

---

## CrmLead fields reference (P4b-GS)

Internal field names used in API responses for clients/leads sourced from Google Sheets cache. See [data-model.md](data-model.md) and [integrations.md](integrations.md) column mapping.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | CrmLead PK |
| `client_name` | string | Client / company name |
| `client_email` | string | Client email (optional) |
| `phone` | string | Client phone |
| `status` | string | Raw CRM status from sheet |
| `deal_amount` | number | Deal value |
| `deal_date` | date (ISO) | Deal or lead date |
| `needs_review` | boolean | Flag for «Клиенты к разбору» |
| `notes` | string | Free-text notes |
| `employee_id` | UUID | Linked user (null until sync/login match) |
| `employee_email` | string | Sheet column value |
| `synced_at` | datetime (ISO) | Last sync timestamp |
| `source_id` | UUID | IntegrationSource reference |

Manager clients API (`GET /manager/clients/`) returns derived review candidates from `CrmLead` where `needs_review=true` or status in `status_review` config, scoped to manager hierarchy.

---

## API-REV-001 — Manager reviews

### Purpose

List and create review records with tasks (REQ-005). Requires manager role + `reviews` module permission.

### `GET /api/v1/manager/reviews/`

Query params: `workspace_id`, `employee_id` (optional filters).

### Response `200`

```json
{
  "count": 1,
  "results": [
    {
      "id": "uuid",
      "employee_id": "uuid",
      "employee_name": "Demo Employee",
      "workspace_id": "uuid",
      "workspace_name": "ОП Москва",
      "author_name": "Demo Manager",
      "client_name": "ООО «Вектор»",
      "comment": "Разбор по качеству",
      "discussion": "Обсудили скрипт",
      "created_at": "2026-06-09T12:00:00Z",
      "tasks": [{ "id": "uuid", "title": "Переслушать звонки", "status": "pending" }],
      "tasks_done": 0,
      "tasks_total": 1
    }
  ]
}
```

### `POST /api/v1/manager/reviews/`

Requires `reviews: edit`. Creates audit event `review_create`.

### Request

```json
{
  "employee_id": "uuid",
  "workspace_id": "uuid",
  "comment": "Комментарий",
  "discussion": "Что обсудили",
  "client_id": "uuid",
  "tasks": ["Задача 1", "Задача 2"]
}
```

### Response `201`

Same shape as list item.

---

## API-REV-002 — Employee task status

### `PATCH /api/v1/employee/tasks/{task_id}/`

Employee updates own task status; reflected in manager review history.

### Request

```json
{ "status": "done" }
```

Values: `pending` | `in_progress` | `done`.

### Response `200`

Task object with `review_id`, `review_date`, `author_name`.

---

## API-AI-001 — Quality criteria

### `GET/POST /api/v1/manager/settings/quality-criteria/`

Requires `settings: view` (GET) or `settings: edit` (POST).

### `PATCH/DELETE .../quality-criteria/{id}/`

Requires `settings: edit`.

---

## API-AI-002 — Analytics reports list

### `GET /api/v1/manager/analytics/reports/`

Requires `analytics: view` or `run`.

---

## API-AI-003 — Run analytics report

### `POST /api/v1/manager/analytics/reports/run/`

Requires `analytics: run`. Body: `workspace_id`, optional `employee_id`, `template`, optional `custom_report_id`.

Returns canvas with stage scores, criteria breakdown, recommendations. Fails with 400 if no transcriptions. When `custom_report_id` is set, template becomes `custom` and criteria are filtered by structured query focus stages.

---

## API-CR-001 — Custom AI reports

### `GET/POST /api/v1/manager/settings/custom-reports/`

Requires `settings: view` (GET) or `settings: edit` (POST). POST body: `title`, `description`. Server structures `structured_query` (MVP: rule-based stage keywords). List/detail scoped to custom reports whose author belongs to a workspace in the actor's manager scope (same pattern as `reports_queryset`).

### `GET/PATCH/DELETE .../custom-reports/{id}/`

Requires `settings: view` (GET) or `settings: edit` (PATCH/DELETE).

---

## API-KB-001 — Knowledge base

### `GET/POST /api/v1/manager/settings/knowledge/`

Requires `settings: view` / `edit`. Materials used by AI agents (RAG keyword search).

### `PATCH/DELETE .../knowledge/{id}/`

Article fields: `title`, `category`, `content`, `tags`, `access_level` (`all` | `manager` | `employee`).

---

## API-AGENT-001 — AI agent chat

### `POST /api/v1/manager/agent/chat/` · `POST /api/v1/employee/agent/chat/`

Requires `agent: use`. Body: `message`, optional `session_id`, `client_name`, `client_note`.

Response: session with `messages` and `sources` on assistant replies.

---

## Related Docs

- [data-model.md](data-model.md) — Tenant, User, integrations entities
- [pages-map.md](../project/design-guide/pages-map.md) — routes after login
