Doc ID: ARCH-INT-001
Status: active
Source of truth: yes
Owner: backend
Related docs: docs/features/data-integration/data-integration.md, docs/architecture/data-model.md, docs/architecture/api-contracts.md, docs/security/secrets-management.md
Update together with: data-integration.md, api-contracts.md, data-model.md
Update trigger: новый внешний источник, adapter, webhook или sync job
Review required: backend, security
Maturity: L2

# Integrations

Внешние источники данных для User Level (STAGE-002). Настройка credentials и column mapping — **Integration Level (Django Admin only)**; отдельного Integration UI в User Level **нет**.

## Sources (MVP)

| Source type | Code | Provides | Adapter |
|---|---|---|---|
| CRM | `crm` | leads, deals, revenue, clients-to-review | **Google Sheets** (P4b-GS production) or demo fallback |
| Telephony | `telephony` | calls, quality_score | demo sync (webhook deferred) |
| Reporting | `reporting` | meetings, revenue | demo sync |

### Production CRM — Google Sheets (P4b-GS, hybrid sync)

First production CRM connector: **Google Sheets API** (read-only). Integrator shares the spreadsheet with the service account email. The backend uses a **hybrid model**:

| Path | When | Behavior |
|---|---|---|
| **Sync** (hourly Celery Beat, Admin action, `POST …/sync/`) | Dashboard metrics + review queue | One sheet read → `MetricSnapshot` (`deals` per employee) + `ClientToReview` for matching `review_rules` |
| **Agent CRM query** | On demand in chat | Live sheet read → in-memory filters (no `CrmLead` bulk cache) |

Typical sync pass for ~100k rows: ~30s–2min depending on sheet size and API latency.

| Data | Sheet source | Maps to |
|---|---|---|
| Deals per employee | Row count assigned via `manager_email` | `MetricSnapshot.metric_key=deals` |
| Clients to review | Rows matching explicit `review_rules` | `ClientToReview` (derived on sync) |
| Agent lookups (list/count/search) | Live read same sheet | In-memory filter; `as_of` = query time |

**Provider:** `google_sheets` in `IntegrationSource.config_json.provider`. Spreadsheet ID in `config_json.spreadsheet_id`.

**Service account:** JSON key with Sheets read scope. Store **per tenant** encrypted in `IntegrationSource.credentials_encrypted` via Django Admin (recommended). Optional global default: `GOOGLE_SERVICE_ACCOUNT_JSON` env path for single-tenant dev — see `.env.example`.

**Column mapping:** Either `header_map` + `header_row` (header text → internal field) **or** `column_map` (Excel letters A/B/C…) + `data_start_row` when headers are not on row 1. Admin form supports both modes.

**Legacy `CrmLead` rows:** Pre-hybrid deployments may still have cached rows. Run `python manage.py purge_google_sheets_crm_leads` after migration. New sync does not write `CrmLead` for Google Sheets.

```json
{
  "provider": "google_sheets",
  "spreadsheet_id": "1abc…",
  "sheet_name": "Leads",
  "header_map": {
    "id лида": "lead_id",
    "lead_id": "lead_id",
    "клиент": "client_name",
    "client_name": "client_name",
    "телефон": "phone",
    "phone": "phone",
    "город": "city",
    "city": "city",
    "комментарий": "communication_comment",
    "communication_comment": "communication_comment",
    "email менеджера": "manager_email",
    "manager_email": "manager_email",
    "email супервайзера": "supervisor_email",
    "supervisor_email": "supervisor_email",
    "этап воронки": "pipeline_stage",
    "pipeline_stage": "pipeline_stage",
    "статус": "status_stage",
    "status_stage": "status_stage",
    "ссылка на записи": "recording_url",
    "recording_url": "recording_url",
    "разбор": "needs_review",
    "needs_review": "needs_review"
  },
  "skip_status_stages": ["done", "closed", "закрыт"],
  "review_rules": {
    "empty_comment_on_active": true,
    "auto_review_statuses": ["требует разбора"]
  },
  "crm_vocabulary": {
    "stages": {
      "Closing": ["closing", "дожатие", "на дожатии"]
    },
    "statuses": {
      "Assigned": ["assigned", "назначен"],
      "open": ["open", "в работе"]
    }
  }
}
```

- **`skip_status_stages`:** closed leads excluded from empty-comment review rule.
- **`review_rules`:** only rows matching at least one rule become `ClientToReview` — **not** all open leads. Rules: sheet `needs_review` column (`TRUE`/`да`), `auto_review_statuses`, optional `empty_comment_on_active`.
- **`crm_vocabulary`:** maps **canonical sheet values** → aliases for NL queries. Structure: `stages` / `statuses` → `{ "Closing": ["closing", "дожатие"], … }`. Used by agent + live `query_crm_leads`.

Employee mapping: sheet `manager_email` ↔ `User.email` (tenant-scoped, active employee/manager). Used for deals snapshots and review queue assignment.

**RegistrationInvite flow:** Integrator pre-creates rows in the sheet with `manager_email`. In Django Admin, create `RegistrationInvite` with matching **Expected email** (optional but recommended), tenant, workspace, and role. Invite **code** auto-generates on save; Admin shows **registration_url** (`FRONTEND_URL/register?code=…`). User submits `email`, `password`, `full_name`, `invite_code` → `POST /auth/register/` → default `ModulePermission` rows by role. Metrics/review sync runs on the next Celery Beat pass, manual **Refresh metrics and review queue**, or `POST …/sync/` — not on register itself.

**Django Admin CRM form (integrator):** structured fields for provider, spreadsheet ID, sheet name, column letters or header labels, and credentials JSON. Collapsed **Advanced JSON** accepts only `review_rules` and `crm_vocabulary`; full `config_json` is assembled on save. List action **Refresh metrics and review queue** for Google Sheets sources.

**No User Level Integration UI:** All CRM setup (service account JSON, spreadsheet ID, column map, invite rows) is **Django Admin only** for MVP. User Level exposes read-only source health via `GET /integrations/sources/` and metrics; manual sync remains `POST /integrations/sources/{id}/sync/` for managers with `settings: edit`.

### Future adapter — amoCRM (P4, deferred for leads)

amoCRM REST adapter (read-only metrics) remains in codebase as **future** full-CRM adapter. P4 shipped `deals`/`revenue` via amoCRM API; **P4b-GS pivots primary CRM to Google Sheets** for leads and pilot onboarding. Re-enable amoCRM when OAuth/subdomain UX is product-ready.

**Not in P4b-GS:** telephony webhook, reporting real adapters, CRM write-back, User Level integration settings pages.

## Google Sheet template

Copy this header row (row 1). Russian **or** English aliases — both supported if listed in `header_map`. Required columns: `lead_id`, `client_name`.

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| `lead_id` | `client_name` | `phone` | `city` | `communication_comment` | `manager_email` | `supervisor_email` | `pipeline_stage` | `status_stage` | `recording_url` |

Optional column for explicit review flag:

| K |
|---|
| `needs_review` |

Example data row:

| lead_id | client_name | phone | city | communication_comment | manager_email | supervisor_email | pipeline_stage | status_stage | recording_url | needs_review |
|---|---|---|---|---|---|---|---|---|---|---|
| `L-100` | ООО «Вектор» | +7 495 000-00-00 | Москва | Нет follow-up 5 дней | `employee@demo.local` | `manager@demo.local` | Qualification | open | https://… | TRUE |

`needs_review`: `TRUE` / `FALSE` or `да` / `нет` — used only when listed in `review_rules`.

## CRM architecture (P4c) — DB cache, not live LLM

User Level APIs and the manager agent read **`CrmLead` in PostgreSQL**, not live Google Sheets rows and **not** batch LLM analysis of all CRM comments. The sheet remains the external system of record; sync jobs refresh the cache.

| Layer | Role |
|---|---|
| Google Sheet | External CRM / ops spreadsheet |
| `CrmLead` | DB cache — query target for dashboards, agent SQL filters, metrics |
| `ClientToReview` | Derived subset per `review_rules` (explicit flags/rules only) |
| Manager agent | NL question → **one** LLM call to structured filters → scoped `CrmLead` query; optional on-demand `refresh_crm` |

**Rejected / deferred:** batch LLM triage of all `communication_comment` rows; 24/7 realtime webhook sync from Sheets.

## Sync strategy (Google Sheets)

**Not realtime.** Multiple trigger paths share one pipeline (`integrations.sync_source` → `run_source_sync()` → Sheets adapter → upsert `CrmLead` → derive `ClientToReview`). No batch LLM over comments; no `MetricSnapshot` from Sheets in P4c.

| Trigger | Schedule / event | Notes |
|---|---|---|
| **Celery Beat** | Every `CRM_SYNC_INTERVAL_MINUTES` (default **60**) | `integrations.sync_all_sources` queues all enabled sources |
| **Login** | `POST /auth/login/` success | Queues tenant CRM sync **if** `last_sync_at` older than interval — **throttled** (skip when fresh) |
| **On-demand** | Manager agent `refresh_crm` tool | Same task; agent may request before answering stale-data questions |
| **Manual** | `POST /integrations/sources/{id}/sync/` | Manager with `settings: edit`; always queues (no throttle) |

Env: `CRM_SYNC_INTERVAL_MINUTES` — see `.env.example`. Beat schedule derived from this value (not daily 01:00 UTC).

**DB cache rules:**

1. Upsert `CrmLead` keyed by `(tenant, integration_source, external_lead_id)`; `synced_at` on each row; `IntegrationSource.last_sync_at` on successful sync.
2. Derive `ClientToReview` only from `review_rules` (see config example) — **not** every open lead.
3. `GET /integrations/metrics/`, `GET /manager/clients/`, agent CRM answers use cache + `as_of: last_sync_at`.

Pipeline:

1. `IntegrationSource` per tenant/workspace with `status`, `config_json`, encrypted credentials.
2. Celery `integrations.sync_source` → adapter reads sheet range → upsert `CrmLead` → `ClientToReview` → metrics (or demo when no credentials).
3. User Level never calls Sheets API on read path.

## Manager agent — on-demand CRM query (P4c)

Manager agent (`POST /manager/agent/chat/`) may invoke CRM tools:

1. **Parse intent** — rule-based filters first (keywords); optional single LLM call for ambiguous NL → structured filter dict. `crm_vocabulary.stages` / `.statuses` expand terms like «дожатие», «назначен» before SQL query.
2. **Query cache** — `integrations.services.crm.query` runs scoped `CrmLead` queryset (tenant + manager hierarchy); returns count, sample rows, aggregates. No per-row LLM on comments.
3. **Optional refresh** — `refresh_crm` queues sync when user asks for «актуальные» data or cache is older than interval.
4. **Answer** — assistant reply includes `as_of` (ISO `IntegrationSource.last_sync_at`) so manager knows data freshness.

Employee agent: KB + recordings only (no CRM query tool in MVP).

## Sync pipeline (all sources)

1. `IntegrationSource` row per tenant/workspace with `status`.
2. Celery task `integrations.sync_source` → `run_source_sync()` writes `CrmLead` / `ClientToReview` (CRM). Telephony/reporting/demo paths still write `MetricSnapshot`.
3. Celery Beat `integrations.sync_all_sources` — interval from `CRM_SYNC_INTERVAL_MINUTES`.
4. Manual trigger: `POST /integrations/sources/{id}/sync/` (manager).
5. Login hook: throttled CRM sync on `POST /auth/login/` (P4c).
6. `GET /integrations/metrics/` aggregates snapshots + source health → `completeness` field.

## Recordings & transcription

| Channel | Code | API |
|---|---|---|
| Telephony ingest | `telephony` | Integration Level webhook (planned) |
| Manual upload | `manual` | `POST /integrations/recordings/` |

Celery task `integrations.transcribe_recording` — OpenRouter STT via `stt_adapter` (demo fallback when no API key). Transient audio on upload, deleted after processing.

Scheduled purge: `integrations.purge_expired_transcripts` — transcripts (90d). `ai.purge_expired_agent_chats` — agent chat sessions (90d, `AGENT_CHAT_RETENTION_DAYS`).

## Storage

| Asset | Location |
|---|---|
| CRM leads (sheet cache) | PostgreSQL `CrmLead` |
| Audio files | **Not persisted** — validated on upload, discarded after processing |
| Transcripts | PostgreSQL `Transcription.text` + `content_json` (90-day retention) |

## Related Docs

- [api-contracts.md](api-contracts.md) — API-INT-*, API-AUTH-005
- [data-model.md](data-model.md) — CrmLead, RegistrationInvite
- [secrets-management.md](../security/secrets-management.md)
