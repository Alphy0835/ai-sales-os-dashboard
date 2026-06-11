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

> STAGE-001–007 entities implemented (auth, integrations, reviews, AI analytics, knowledge, agents, custom reports).

## Entity Index

| Entity | Purpose | Stored where | Feature | Sensitivity |
|---|---|---|---|---|
| Tenant | SaaS customer org | PostgreSQL | FEAT-001 | internal |
| Workspace | Subdivision scope | PostgreSQL | FEAT-001 | internal |
| User | Login identity + role | PostgreSQL | FEAT-001 | personal |
| ModulePermission | Granular module access | PostgreSQL | FEAT-001 | internal |
| ManagerScope | Manager workspace scope | PostgreSQL | FEAT-001 | internal |
| AuditLog | Permission changes, scope-denied, review-create events | PostgreSQL | FEAT-001, FEAT-004 | internal |
| IntegrationSource | CRM/telephony/reporting connector | PostgreSQL | FEAT-002 | internal |
| CrmLead | Cached CRM row from Google Sheet | PostgreSQL | FEAT-002, FEAT-003 | internal |
| RegistrationInvite | One-time employee/manager signup token | PostgreSQL | FEAT-001 | internal |
| MetricSnapshot | Daily metric values per source | PostgreSQL | FEAT-002 | internal |
| ConversationRecording | Call/meeting metadata (no audio file) | PostgreSQL | FEAT-002 | confidential |
| Transcription | Speech-to-text for AI analytics | PostgreSQL | FEAT-002 | confidential |
| ClientToReview | Clients flagged for manager review | PostgreSQL | FEAT-003 | internal |
| Review | Manager review session with employee | PostgreSQL | FEAT-004 | internal |
| ReviewTask | Task assigned during a review | PostgreSQL | FEAT-004 | internal |
| QualityCriterion | Tenant rule for AI quality scoring | PostgreSQL | FEAT-005 | internal |
| AnalyticsReport | Stored AI analytics canvas | PostgreSQL | FEAT-005, FEAT-007 | confidential |
| CustomReport | Saved natural-language report definition | PostgreSQL | FEAT-007 | internal |
| KnowledgeArticle | RAG material for AI agents | PostgreSQL | FEAT-006 | confidential |
| KnowledgeArticleGrant | Per-user KB article access override | PostgreSQL | FEAT-001, FEAT-006 | internal |
| AgentChatSession | AI agent dialog session | PostgreSQL | FEAT-006 | confidential |
| AgentChatMessage | Messages in agent session | PostgreSQL | FEAT-006 | confidential |

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

Audit trail for permission changes, scope-denied access attempts, and review creation (REQ-NFR-001).

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | PK |
| tenant_id | UUID FK | yes | Tenant |
| actor_id | UUID FK | yes | User who performed action |
| target_user_id | UUID FK | no | Affected user |
| action | enum | yes | `permission_change` \| `scope_denied` \| `review_create` |
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

Connector status per tenant/workspace. Configuration secrets — Integration Level (Django Admin only; no User Level Integration UI).

| Field | Type | Description |
|---|---|---|
| source_type | enum | `crm` \| `telephony` \| `reporting` |
| status | enum | `connected` \| `degraded` \| `disconnected` \| `error` |
| external_id | string | Spreadsheet ID (Google Sheets) or external account id |
| credentials_encrypted | text | Fernet-encrypted service account JSON (CRM) |
| config_json | json | See `config_json` fields below |
| last_sync_at | datetime | Last successful/partial sync (`as_of` for agent + metrics) |
| last_error | text | Last error message |

### `config_json` fields (CRM / Google Sheets)

| Key | Purpose |
|---|---|
| `provider` | `google_sheets` \| `amocrm` \| `demo` |
| `spreadsheet_id` | Google Sheet id |
| `sheet_name` | Tab name (default `Leads`) |
| `header_map` | Sheet header → `CrmLead` field |
| `skip_status_stages` | Closed stages excluded from `ClientToReview` (still cached) |
| `review_rules` | Explicit rules for `ClientToReview` derivation |
| `crm_vocabulary` | Business term → filter values for manager-agent NL parsing |

Example `review_rules`:

```json
{
  "empty_comment_on_active": true,
  "auto_review_statuses": ["требует разбора", "needs_review"]
}
```

Sheet column `needs_review` (`TRUE` / `да`) is always honoured when mapped in `header_map`.

Example `crm_vocabulary`:

```json
{
  "stages": {
    "Closing": ["closing", "дожатие", "на дожатии"]
  },
  "statuses": {
    "Assigned": ["assigned", "назначен"],
    "open": ["open", "в работе"]
  }
}
```

Canonical keys (`Closing`, `Assigned`) must match values stored in the sheet / `CrmLead` after sync.

---

## Entity: CrmLead

Cached row from Google Sheets CRM sync (P4b-GS / P4c). **DB cache** for User Level reads and manager-agent SQL-style filters — not live Sheets API, not batch LLM over comments.

### Purpose

Store per-lead CRM data for dashboards, scoped agent queries, reviews, and metrics. Synced by `integrations.sync_source` (hourly Beat, throttled login, manual, agent `refresh_crm`).

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | PK |
| tenant_id | UUID FK | yes | Tenant |
| workspace_id | UUID FK | no | Workspace (from employee or source default) |
| integration_source_id | UUID FK | yes | CRM `IntegrationSource` |
| external_lead_id | string | yes | Stable sheet id (`lead_id` column) |
| employee_id | UUID FK User | no | Linked user after `manager_email` match |
| client_name | string | yes | Client / company name |
| phone | string | no | Client phone |
| city | string | no | City |
| communication_comment | text | no | CRM comment (stored; not LLM-triaged in batch) |
| pipeline_stage | string | no | Funnel stage |
| status_stage | string | no | Lead status |
| recording_url | string | no | Recording URL |
| manager_email | string | no | Sheet manager email |
| supervisor_email | string | no | Sheet supervisor email |
| synced_at | datetime | yes | Last upsert from sync job |

### Query model (P4c)

Manager-agent and internal services filter via `integrations.services.crm.query`:

- Scope: `tenant_id` + manager hierarchy (`employee`, `workspace`).
- Filters: `pipeline_stage`, `status_stage`, `city`, `manager_email`, `employee_id`, `client_name` (icontains).
- Aggregates: `count`, limited `list` — against PostgreSQL only.
- Freshness: answers cite `IntegrationSource.last_sync_at` as `as_of`.

### Relations

- Many CrmLead → one IntegrationSource, one Tenant.
- Optional link to User via `employee_id` (set when `manager_email` matches active user).

### Validation

- Unique (`tenant_id`, `integration_source_id`, `external_lead_id`).

### Deletion

Hard delete on tenant purge; rows upserted on each sync (stale row policy per adapter).

---

## Entity: ClientToReview

Manager dashboard queue («Клиенты к разбору»). **P4c:** derived on CRM sync only when row matches explicit `review_rules` in `IntegrationSource.config_json` (e.g. `needs_review` column = true/да) — **not** all open leads.

| Field | Type | Description |
|---|---|---|
| tenant_id | FK | Tenant |
| workspace_id | FK | Workspace |
| employee_id | FK | Assigned employee |
| client_name | string | Display name |
| client_external_id | string | `CrmLead.external_lead_id` |
| reason | text | From sheet comment / rule label |
| priority | enum | `high` \| `medium` \| `low` |
| status | enum | `new` \| `in_progress` \| `done` |

Populated by sync adapter when `review_rules` match; excluded when `status_stage` in `skip_status_stages`.

---

## Entity: RegistrationInvite

One-time signup token for employees (and optionally managers) onboarded via Google Sheet + Django Admin (P4b-GS). No self-service tenant signup in MVP.

### Purpose

Allow invited users to create a password and `User` row without integrator manually setting passwords. Optional `expected_email` ties registration to sheet `manager_email`.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | PK |
| code | string | yes | Invite code (auto-generated on save if blank; unique) |
| expected_email | string | no | If set, registration email must match |
| tenant_id | UUID FK | yes | Tenant |
| workspace_id | UUID FK | yes | ОП (workspace); обязателен для invite — без него manager scope не создаётся |
| role | enum | yes | `manager` \| `employee` |
| expires_at | datetime | yes | Invite expiry |
| max_uses | int | yes | Max successful registrations (default 1) |
| use_count | int | yes | Successful registrations so far |
| used_at | datetime | no | Set on first successful registration |
| created_by_id | UUID FK User | no | Admin who issued invite |
| created_at | datetime | yes | Audit |

### Relations

- Registration consumes invite → creates `User` + default `ModulePermission` rows (role-based; manager also gets `ManagerScope` for invite workspace).
- Post-registration login triggers CRM sync (if not throttled) to link `CrmLead.employee_id` via `manager_email`.

### Validation

- `POST /auth/register/` rejects expired invites or when `use_count >= max_uses`; rejects email mismatch when `expected_email` is set.

### Deletion

Expired unused invites purged by periodic job (post-MVP) or manual Admin cleanup.

---

## Entity: MetricSnapshot

Daily metric pulled from a source for an employee. Aggregated by `GET /integrations/metrics/`.

Keys: `calls`, `deals`, `revenue`, `meetings`, `quality_score`.

---

## Entity: ConversationRecording / Transcription

Recording linked to employee + client in scope. **Audio files are not stored** — only metadata and derived transcript text in PostgreSQL.

| Aspect | Rule |
|---|---|
| Audio | Not persisted; validated on upload (size/type); discarded after processing |
| Transcript | `Transcription.text`, `content_json` |
| Retention | **90 days** — hard delete via Celery `integrations.purge_expired_transcripts` (`TRANSCRIPT_RETENTION_DAYS`) |
| ASR | MVP demo text in `content_json`; production STT adapter deferred |

Transcription task: `integrations.transcribe_recording` (demo path today).

---

## Entity: KnowledgeArticleGrant

Per-user override for knowledge base article access (REQ-013/014, API-PERM-004). Complements article-level `access_level` (`all` / `manager` / `employee`).

| Field | Type | Required | Description |
|---|---|---|---|
| id | UUID | yes | PK |
| tenant_id | UUID FK | yes | Tenant |
| user_id | UUID FK | yes | Grant subject |
| article_id | UUID FK | yes | Knowledge article |
| is_allowed | bool | yes | Allow (true) or deny (false) override |
| created_at / updated_at | datetime | yes | Audit |

Unique (`user_id`, `article_id`). Managed via `PUT /api/v1/permissions/users/{id}/knowledge/` and PAGE-006 Access tab.

Implementation: `apps/api/ai/models.py`, `ai/services/knowledge_grants.py`.

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

Every query on tenant-scoped tables MUST filter by authenticated user's `tenant_id`.

**Enforcement (C2):** tenant and workspace isolation is applied in **views and service querysets** (e.g. `recordings_queryset`, `reports_queryset`, `custom_reports_queryset`) — **not** via Django custom managers on models. There is no `TenantManager` or automatic queryset scoping at the ORM layer.

`TenantMiddleware` (`apps/api/core/middleware.py`) attaches `request.tenant` from the authenticated user for convenience only; it does not filter queries. Views and services rely on explicit `user.tenant_id` (and workspace scope helpers) in each endpoint.

Cross-tenant access is prevented by code review + API tests (including `ai/tests/test_security_scope.py`).

## Related Docs

- [api-contracts.md](api-contracts.md)
- [user-roles.md](../project/user-roles.md)
