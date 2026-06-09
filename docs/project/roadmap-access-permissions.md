Doc ID: ROADMAP-STAGE-001
Status: active
Source of truth: yes
Owner: backend
Related docs: docs/project/roadmap.md, docs/features/access-permissions/access-permissions.md, docs/architecture/api-contracts.md
Update trigger: изменение auth/scope/permissions implementation
Review required: backend, security, QA

# STAGE-001 — Access & Permissions (Implementation)

**Completed:** 2026-06-09

## Summary

User Level auth, manager hierarchy with workspace scope, permission grant API with ceiling rule, and audit logging.

## Code

| Area | Path |
|---|---|
| Models | `apps/api/accounts/models.py` — User.manager, ManagerScope, ModulePermission, AuditLog |
| Scope | `apps/api/accounts/services/scope.py` |
| Ceiling / grant | `apps/api/accounts/services/permissions.py`, `grant.py` |
| Audit | `apps/api/accounts/services/audit.py` |
| API | `apps/api/accounts/views.py`, `urls.py` |
| Tests | `apps/api/accounts/tests/test_stage001.py` |
| Seed | `python manage.py seed_demo` |

## API Endpoints

- Auth: API-AUTH-001 … 004
- Scope: API-SCOPE-001, API-SCOPE-002
- Permissions: API-PERM-001 … 003
- Audit: API-AUDIT-001

See [api-contracts.md](../architecture/api-contracts.md).

## Demo Hierarchy

| User | Password | Role | Scope |
|---|---|---|---|
| manager@demo.local | demo1234 | Top manager | ОП Москва + ОП СПб |
| regional@demo.local | demo1234 | Sub-manager | ОП Москва only (reports to top) |
| employee@demo.local | demo1234 | Employee | ОП Москва |
| employee-spb@demo.local | demo1234 | Employee | ОП СПб (outside regional scope) |

## Ceiling Rule

Implemented per `user-roles.md`: grantor level rank per module must be ≥ requested level. Violations return `400` with field errors.

## QA

Automated: `python manage.py test accounts.tests.test_stage001`  
Manual QA-AC: pending formal sign-off in acceptance-criteria tracker.

## Related Docs

- [roadmap.md](../project/roadmap.md)
- [access-permissions.md](../features/access-permissions/access-permissions.md)
