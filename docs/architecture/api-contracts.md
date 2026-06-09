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
Auth default: `Authorization: Bearer {access_token}`  
OpenAPI: `/api/schema/` (drf-spectacular)

> STAGE-001 auth/scope + STAGE-002 integrations. Dashboard UI endpoints — STAGE-003.

## API Index

| API ID | Method | Path | Purpose | Auth | Feature |
|---|---|---|---|---|---|
| API-HEALTH-001 | GET | `/health/` | Liveness | no | — |
| API-AUTH-001 | POST | `/auth/login/` | Login, issue JWT | no | FEAT-001 |
| API-AUTH-002 | POST | `/auth/refresh/` | Refresh access token | refresh body | FEAT-001 |
| API-AUTH-003 | GET | `/auth/me/` | Current user + permissions + scope | yes | FEAT-001 |
| API-AUTH-004 | POST | `/auth/logout/` | Client-side logout ack | yes | FEAT-001 |
| API-SCOPE-001 | GET | `/scope/` | Workspaces and users in scope | yes | FEAT-001 |
| API-SCOPE-002 | GET | `/scope/users/{id}/` | Check user access in scope | yes | FEAT-001 |
| API-PERM-001 | GET | `/permissions/users/` | List users in scope + permissions | yes (settings view/edit) | FEAT-001 |
| API-PERM-002 | GET | `/permissions/users/{id}/` | User permissions detail | yes (settings view/edit) | FEAT-001 |
| API-PERM-003 | PUT | `/permissions/users/{id}/` | Grant permissions (ceiling rule) | yes (settings edit) | FEAT-001 |
| API-AUDIT-001 | GET | `/audit/permissions/` | Permission change audit log | yes (settings view/edit) | FEAT-001 |
| API-INT-001 | GET | `/integrations/sources/` | Integration sources + health | yes (dashboard view) | FEAT-002 |
| API-INT-002 | GET | `/integrations/metrics/` | Aggregated metrics + completeness | yes (dashboard view) | FEAT-002 |
| API-INT-003 | GET | `/integrations/recordings/` | Recordings in scope | yes (dashboard view) | FEAT-002 |
| API-INT-004 | POST | `/integrations/recordings/` | Manual recording upload | yes (dashboard view) | FEAT-002 |
| API-INT-005 | GET | `/integrations/recordings/{id}/` | Recording detail | yes (dashboard view) | FEAT-002 |
| API-INT-006 | GET | `/integrations/recordings/{id}/transcription/` | Transcription text | yes (dashboard view) | FEAT-002 |
| API-INT-007 | POST | `/integrations/recordings/{id}/transcription/` | Queue (re)transcription | yes (dashboard view) | FEAT-002 |
| API-MGR-001 | GET | `/manager/dashboard/` | Manager dashboard aggregate | yes (manager, dashboard view) | FEAT-003 |
| API-MGR-002 | GET | `/manager/clients/` | Clients to review | yes (manager, dashboard view) | FEAT-003 |
| API-EMP-001 | GET | `/employee/dashboard/` | Employee personal metrics | yes (employee, dashboard view) | FEAT-003 |

---

## API-HEALTH-001 — Health

### Response `200`

```json
{ "status": "ok", "service": "ai-sales-os-api" }
```

---

## API-AUTH-001 — Login

### Purpose

Authenticate User Level user; return JWT pair and role for frontend routing.

### Authorization

Public.

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

### Errors

| Code | Meaning | Client behavior |
|---|---|---|
| 400 | Validation error | Show field errors |
| 401 | Invalid credentials | Show login error |

---

## API-AUTH-002 — Refresh

### Request

```json
{ "refresh": "<jwt_refresh>" }
```

### Response `200`

```json
{
  "access": "<new_jwt_access>"
}
```

### Errors

| Code | Meaning |
|---|---|
| 401 | Invalid/expired refresh |

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

Acknowledge logout (MVP: stateless JWT; client clears tokens).

### Response `204`

No body.

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

## API-AUDIT-001 — Permission audit log

### Query params

| Param | Description |
|---|---|
| `user_id` | Filter by target user (optional) |
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

## Related Docs

- [data-model.md](data-model.md) — Tenant, User, integrations entities
- [pages-map.md](../project/design-guide/pages-map.md) — routes after login
