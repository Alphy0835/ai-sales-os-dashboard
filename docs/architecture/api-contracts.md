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

> STAGE-001 scope only. Dashboard/integration endpoints — later stages.

## API Index

| API ID | Method | Path | Purpose | Auth | Feature |
|---|---|---|---|---|---|
| API-HEALTH-001 | GET | `/health/` | Liveness | no | — |
| API-AUTH-001 | POST | `/auth/login/` | Login, issue JWT | no | FEAT-001 |
| API-AUTH-002 | POST | `/auth/refresh/` | Refresh access token | refresh body | FEAT-001 |
| API-AUTH-003 | GET | `/auth/me/` | Current user + permissions | yes | FEAT-001 |
| API-AUTH-004 | POST | `/auth/logout/` | Client-side logout ack | yes | FEAT-001 |

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

## Related Docs

- [data-model.md](data-model.md) — Tenant, User, ModulePermission
- [pages-map.md](../project/design-guide/pages-map.md) — routes after login
