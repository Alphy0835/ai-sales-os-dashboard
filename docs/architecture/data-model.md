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

> STAGE-001 auth entities + STAGE-002 integration entities. Reviews, knowledge — later stages.

## Entity Index

| Entity | Purpose | Stored where | Feature | Sensitivity |
|---|---|---|---|---|
| Tenant | SaaS customer org | PostgreSQL | FEAT-001 | internal |
| Workspace | Subdivision scope | PostgreSQL | FEAT-001 | internal |
| User | Login identity + role | PostgreSQL | FEAT-001 | personal |
| ModulePermission | Granular module access | PostgreSQL | FEAT-001 | internal |
| ManagerScope | Manager workspace scope | PostgreSQL | FEAT-001 | internal |
| AuditLog | Permission and scope-denied events | PostgreSQL | FEAT-001 | internal |
| IntegrationSource | CRM/telephony/reporting connector | PostgreSQL | FEAT-002 | internal |
| MetricSnapshot | Daily metric values per source | PostgreSQL | FEAT-002 | internal |
| ConversationRecording | Call/meeting audio metadata | PostgreSQL + media | FEAT-002 | confidential |
| Transcription | Speech-to-text for AI analytics | PostgreSQL | FEAT-002 | confidential |
| ClientToReview | Clients flagged for manager review | PostgreSQL | FEAT-003 | internal |

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

## Entity: IntegrationSource

Connector status per tenant/workspace. Configuration secrets — Integration Level (not stored in User Level API).

| Field | Type | Description |
|---|---|---|
| source_type | enum | `crm` \| `telephony` \| `reporting` |
| status | enum | `connected` \| `degraded` \| `disconnected` \| `error` |
| last_sync_at | datetime | Last successful/partial sync |
| last_error | text | Last error message |

---

## Entity: MetricSnapshot

Daily metric pulled from a source for an employee. Aggregated by `GET /integrations/metrics/`.

Keys: `calls`, `deals`, `revenue`, `meetings`, `quality_score`.

---

## Entity: ConversationRecording / Transcription

Recording linked to employee + client in scope. Transcription generated by Celery task (`integrations.transcribe_recording`). MVP uses demo transcript text; production STT — post-MVP adapter.

---

## Entity: Review

Manager-led review session with an employee (REQ-005).

| Field | Type | Description |
|---|---|---|
| tenant_id | FK | Tenant |
| workspace_id | FK | Workspace |
| employee_id | FK | Review subject |
| author_id | FK | Manager who created |
| client_to_review_id | FK | Optional link to `ClientToReview` |
| comment | text | Summary comment |
| discussion | text | What was discussed |
| created_at | datetime | Review date |

---

## Entity: ReviewTask

Task assigned during a review; shown on employee dashboard (REQ-006).

| Field | Type | Description |
|---|---|---|
| review_id | FK | Parent review |
| title | string | Task description |
| status | enum | `pending` \| `in_progress` \| `done` |
| completed_at | datetime | Set when status = done |

---

## Entity: QualityCriterion

Tenant-scoped rule for AI quality scoring (REQ-008). MVP: keyword match in transcripts.

| Field | Type | Description |
|---|---|---|
| funnel_stage | enum | greeting, discovery, presentation, objections, closing |
| keywords | text | Comma-separated match tokens |
| is_active | bool | Used in report generation |

---

## Entity: AnalyticsReport

Stored AI analytics result with JSON canvas (REQ-007).

| Field | Type | Description |
|---|---|---|
| template | enum | standard_quality, funnel_dynamics, custom |
| custom_report_id | FK | Optional link to saved CustomReport |
| canvas | json | stages, criteria scores, recommendations |
| employee_id | FK | Optional drill-down subject |

---

## Entity: CustomReport

Saved natural-language report definition (REQ-009). MVP structuring via rule-based keyword → funnel stage mapping.

| Field | Type | Description |
|---|---|---|
| title | string | Display name |
| description | text | Manager's natural language prompt |
| structured_query | json | `focus_stages`, `focus_keywords`, `engine` |
| is_active | bool | Available for analytics run |

---

## Entity: KnowledgeArticle

RAG material for AI agents (REQ-010).

| Field | Type | Description |
|---|---|---|
| category | enum | product, objection, infopovod, case, other |
| access_level | enum | all, manager, employee |
| tags | text | Comma-separated search tokens |

---

## Entity: AgentChatSession / AgentChatMessage

Agent dialog state (REQ-011, REQ-012). Messages include `sources` JSON on assistant replies.

---

## Multi-tenant rule

Every query on tenant-scoped tables MUST filter by authenticated user's `tenant_id`. Enforced via middleware + custom managers (see `apps/api/core`).

## Related Docs

- [api-contracts.md](api-contracts.md)
- [user-roles.md](../project/user-roles.md)
