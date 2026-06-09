Doc ID: SECURITY-AUDIT-001
Status: active
Source of truth: yes
Owner: security
Related docs: docs/features/access-permissions/access-permissions.md, docs/architecture/data-model.md, docs/security/auth-and-access-control.md
Update together with: auth-and-access-control.md, data-model.md, FEAT-001
Update trigger: новый audited event, изменение retention или полей лога
Review required: security, backend
Maturity: L2

# Audit Logging

Правила аудита важных действий User Level (STAGE-001).

## Logged Events (MVP)

| Event | Action code | When | Stored fields |
|---|---|---|---|
| Permission change | `permission_change` | `PUT /permissions/users/{id}/` changes a module level | actor, target_user, module, old_level, new_level, tenant, IP, timestamp |
| Scope denied | `scope_denied` | Access to user outside actor scope (e.g. `GET /scope/users/{id}/`) | actor, target_user, tenant, IP, timestamp |

## Not Logged

- Passwords, JWT tokens, refresh tokens, API secrets
- Full request bodies with credentials

## API

`GET /api/v1/audit/permissions/` — requires `settings: view` or `settings: edit`. See [api-contracts.md](../architecture/api-contracts.md) API-AUDIT-001.

## Retention

MVP: indefinite in PostgreSQL. Archival policy — post-MVP (operations).

## Related Docs

- [auth-and-access-control.md](auth-and-access-control.md)
- [data-model.md](../architecture/data-model.md) — AuditLog entity
