Doc ID: ARCH-DM-001
Status: active
Source of truth: yes
Owner: backend
Related docs: docs/architecture/api-contracts.md, docs/project/user-roles.md, docs/project/terminology.md, docs/security/data-classification.md
Update together with: api-contracts.md, backend-docs.md
Update trigger: новая сущность, поле, связь или правило удаления
Review required: backend, security
Maturity: L2

# Data Model

> STAGE-001 entities only. KPI, reviews, knowledge — later stages.

## Entity Index

| Entity | Purpose | Stored where | Feature | Sensitivity |
|---|---|---|---|---|
| Tenant | SaaS customer org | PostgreSQL | FEAT-001 | internal |
| Workspace | Subdivision scope | PostgreSQL | FEAT-001 | internal |
| User | Login identity + role | PostgreSQL | FEAT-001 | personal |
| ModulePermission | Granular module access | PostgreSQL | FEAT-001 | internal |
| ManagerScope | Manager workspace scope | PostgreSQL | FEAT-001 | internal |
| AuditLog | Permission and scope-denied events | PostgreSQL | FEAT-001 | internal |

## Entity: Tenant

### Purpose

Top-level SaaS isolation. All tenant-scoped rows reference `tenant_id`.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | PK |
| name | string | yes | Company display name |
| slug | string | yes | Unique subdomain key (future) |
| is_active | bool | yes | Soft disable tenant |
| created_at | datetime | yes | Audit |

### Relations

- One Tenant → many Workspaces, Users.

### Deletion

Deactivate (`is_active=false`); hard delete — admin-only, post-MVP.

---

## Entity: Workspace

### Purpose

Subdivision scope for manager/employee (e.g. «ОП Москва»). MVP: one workspace per demo tenant.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | PK |
| tenant_id | UUID FK | yes | Tenant |
| name | string | yes | Display name |
| is_active | bool | yes | |

### Relations

- Workspace belongs to Tenant.
- Users optionally linked to primary workspace.

---

## Entity: User

### Purpose

User Level account (Manager or Employee). Extends Django auth with tenant scope.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | PK |
| tenant_id | UUID FK | yes | Tenant isolation |
| workspace_id | UUID FK | no | Primary workspace |
| email | string | yes | Login identifier (globally unique on MVP) |
| password_hash | string | yes | Django hashed |
| full_name | string | yes | Display |
| role | enum | yes | `manager` \| `employee` |
| manager_id | UUID FK User | no | Parent manager (hierarchy) |
| is_active | bool | yes | |
| is_staff | bool | yes | Django admin (integrator) |
| created_at | datetime | yes | |

### Relations

- User belongs to Tenant, optional Workspace.
- User has many ModulePermission rows.

### Validation

- Email globally unique on MVP (login by email only); tenant scoping via `tenant_id` on user row.
- Employee cannot receive permission broader than grantor (ceiling rule) — enforced in `accounts/services/grant.py` on `PUT /permissions/users/{id}/`.

---

## Entity: ManagerScope

### Purpose

Links a manager to workspaces they can access (hierarchy scope). Sub-manager scope must be a subset of parent manager scope.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | PK |
| user_id | UUID FK | yes | Manager user |
| workspace_id | UUID FK | yes | Accessible workspace |

### Relations

- Unique (`user_id`, `workspace_id`).

---

## Entity: AuditLog

### Purpose

Audit trail for permission changes and scope-denied access attempts (REQ-NFR-001).

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | PK |
| tenant_id | UUID FK | yes | Tenant |
| actor_id | UUID FK | yes | User who performed action |
| target_user_id | UUID FK | no | Affected user |
| action | enum | yes | `permission_change` \| `scope_denied` |
| module | string | no | Module key (permission changes) |
| old_level | string | no | Previous level |
| new_level | string | no | New level |
| ip_address | string | no | Client IP |
| created_at | datetime | yes | |

---

## Entity: ModulePermission

### Purpose

Per-user access to functional modules (dashboard, clients, reviews, analytics, settings, agent).

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | PK |
| user_id | UUID FK | yes | |
| module | enum | yes | `dashboard`, `clients`, `reviews`, `analytics`, `settings`, `agent` |
| level | enum | yes | `none`, `view`, `edit`, `run`, `use` |

### Relations

- Unique (`user_id`, `module`).

### Notes

Default sets created on user seed / invite. Maps to API `/auth/me/` `permissions` object.

---

## Multi-tenant rule

Every query on tenant-scoped tables MUST filter by authenticated user's `tenant_id`. Enforced via middleware + custom managers (see `apps/api/core`).

## Related Docs

- [api-contracts.md](api-contracts.md)
- [user-roles.md](../project/user-roles.md)
