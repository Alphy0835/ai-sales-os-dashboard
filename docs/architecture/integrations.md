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

### Production CRM — Google Sheets (P4b-GS)

First production CRM connector: **Google Sheets API** (read-only). Integrator shares the spreadsheet with the service account email; backend reads rows and caches them in PostgreSQL (`CrmLead`).

| Data | Sheet source | Maps to |
|---|---|---|
| Lead / client rows | One row per deal or client | `CrmLead` (DB cache) |
| `deals` | Count of won rows per employee for period | `MetricSnapshot.metric_key=deals` |
| `revenue` | Sum of deal amounts for period | `MetricSnapshot.metric_key=revenue` |
| Clients to review | Rows with `needs_review=true` or status in review set | `ClientToReview` (derived on sync) |

**Provider:** `google_sheets` in `IntegrationSource.config_json.provider`. Spreadsheet ID in `external_id` (or `config_json.spreadsheet_id`).

**Service account:** JSON key with Sheets read scope. Store **per tenant** encrypted in `IntegrationSource.credentials_encrypted` via Django Admin (recommended). Optional global default: `GOOGLE_SERVICE_ACCOUNT_JSON` env path for single-tenant dev — see `.env.example`.

**Column mapping:** `IntegrationSource.config_json.column_map` — sheet header → internal field. Headers may be Russian or English; mapping is explicit (no auto-detect in MVP).

```json
{
  "provider": "google_sheets",
  "spreadsheet_id": "1abc…",
  "sheet_name": "Leads",
  "header_row": 1,
  "column_map": {
    "email_сотрудника": "employee_email",
    "employee_email": "employee_email",
    "клиент": "client_name",
    "client_name": "client_name",
    "телефон": "phone",
    "phone": "phone",
    "статус": "status",
    "status": "status",
    "сумма": "deal_amount",
    "deal_amount": "deal_amount",
    "дата_сделки": "deal_date",
    "deal_date": "deal_date",
    "разбор": "needs_review",
    "needs_review": "needs_review",
    "примечание": "notes",
    "notes": "notes"
  },
  "status_won": ["выигран", "won", "closed_won"],
  "status_review": ["в работе", "in_progress", "требует разбора"]
}
```

Employee mapping: `CrmLead.employee_email` or `User.email` / `User.external_id` ↔ sheet `employee_email` column.

**RegistrationInvite flow:** Manager (or integrator) pre-creates rows in the sheet with `employee_email`. Integrator creates `RegistrationInvite` in Django Admin (or via future manager API) with matching email + tenant/workspace/role. Employee opens invite link → `POST /auth/register/` → account created → first login triggers CRM sync and links user to sheet rows by email.

**No User Level Integration UI:** All CRM setup (service account JSON, spreadsheet ID, column map, invite rows) is **Django Admin only** for MVP. User Level exposes read-only source health via `GET /integrations/sources/` and metrics; manual sync remains `POST /integrations/sources/{id}/sync/` for managers with `settings: edit`.

### Future adapter — amoCRM (P4, deferred for leads)

amoCRM REST adapter (read-only metrics) remains in codebase as **future** full-CRM adapter. P4 shipped `deals`/`revenue` via amoCRM API; **P4b-GS pivots primary CRM to Google Sheets** for leads and pilot onboarding. Re-enable amoCRM when OAuth/subdomain UX is product-ready.

**Not in P4b-GS:** telephony webhook, reporting real adapters, CRM write-back, User Level integration settings pages.

## Google Sheet template

Copy this header row (row 1). Russian **or** English aliases — both supported if listed in `column_map`.

| A | B | C | D | E | F | G | H | I |
|---|---|---|---|---|---|---|---|---|
| `email_сотрудника` | `клиент` | `телефон` | `email_клиента` | `статус` | `сумма` | `дата_сделки` | `разбор` | `примечание` |

English equivalent:

| A | B | C | D | E | F | G | H | I |
|---|---|---|---|---|---|---|---|---|
| `employee_email` | `client_name` | `phone` | `client_email` | `status` | `deal_amount` | `deal_date` | `needs_review` | `notes` |

Example data row:

| employee_email | client_name | phone | client_email | status | deal_amount | deal_date | needs_review | notes |
|---|---|---|---|---|---|---|---|---|
| `employee@demo.local` | ООО «Вектор» | +7 495 000-00-00 | info@vector.ru | в работе | 150000 | 2026-06-01 | TRUE | Нет follow-up 5 дней |

`needs_review`: `TRUE` / `FALSE` or `да` / `нет`. `status` won values configured in `status_won` (e.g. `выигран`, `won`).

## Sync strategy (Google Sheets)

Three layers — **DB cache** is source of truth for User Level APIs; sheet is external system of record.

1. **DB cache:** Each sync upserts `CrmLead` rows keyed by `(tenant, source, external_row_id)`. `synced_at` and optional `raw_json` store last snapshot. Metrics job aggregates won rows into `MetricSnapshot`.
2. **Celery Beat:** `integrations.sync_all_sources` — daily 01:00 UTC (same schedule as P4). Refreshes all enabled `IntegrationSource` with `source_type=crm`.
3. **Sync on login:** After successful `POST /auth/login/`, queue `integrations.sync_source` for tenant's CRM source (async, non-blocking). Ensures fresh leads on first session of the day without waiting for Beat.

Manual trigger unchanged: `POST /integrations/sources/{id}/sync/` (manager, `settings: edit`).

Pipeline:

1. `IntegrationSource` row per tenant/workspace with `status`, `config_json`, encrypted credentials.
2. Celery task `integrations.sync_source` → `run_source_sync()` → Google Sheets adapter reads range → upsert `CrmLead` → aggregate `MetricSnapshot` (or demo when no credentials).
3. `GET /integrations/metrics/` and manager clients APIs read from DB cache, not live Sheets.

## Sync pipeline (all sources)

1. `IntegrationSource` row per tenant/workspace with `status`.
2. Celery task `integrations.sync_source` → `run_source_sync()` writes `MetricSnapshot` rows and (for CRM) `CrmLead` rows.
3. Celery Beat `integrations.sync_all_sources` — daily 01:00 UTC.
4. Manual trigger: `POST /integrations/sources/{id}/sync/` (manager).
5. Login hook: CRM sync queued on `POST /auth/login/` (P4b-GS).
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
