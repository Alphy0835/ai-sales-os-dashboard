Doc ID: ROADMAP-STAGE-002
Status: active
Source of truth: yes
Owner: backend
Related docs: docs/project/roadmap.md, docs/features/data-integration/data-integration.md, docs/architecture/integrations.md
Update trigger: новый adapter, endpoint или sync job
Review required: backend, QA

# STAGE-002 — Data Integration (Implementation)

**Completed:** 2026-06-09 (backend MVP) · **P4b-GS + P4c:** 2026-06-10 (Google Sheets production CRM)

## Summary

Integration sources with health status, metric aggregation API with partial/empty states, manual recording upload + Celery transcription pipeline.

**Production CRM (pilot path):** Google Sheets adapter (**P4b-GS**) — read-only sync into `CrmLead` DB cache; on-demand refresh via login throttle, Beat, manual sync, and manager agent `refresh_crm` (**P4c**). **Not demo-only.**

Telephony and reporting adapters remain **demo sync** until product decision (see wishlist in [roadmap.md](roadmap.md)).

## Code

| Area | Path |
|---|---|
| Django app | `apps/api/integrations/` |
| Models | IntegrationSource, CrmLead, MetricSnapshot, ConversationRecording, Transcription |
| CRM adapters | `integrations/services/crm/google_sheets.py` (production), `amocrm.py` (deferred) |
| Sync | `integrations/services/sync.py`, tasks `integrations.sync_source`, `integrations.sync_all_sources` |
| On-demand (P4c) | Login hook, `POST …/sync/`, agent `refresh_crm` |
| Aggregation | `integrations/services/aggregation.py` |
| Transcription | `integrations/tasks.py` → `transcribe_recording` |
| Admin templates | `integrations/config_templates.py` — pre-filled Google Sheets `config_json` |
| Seed (dev only) | `python manage.py seed_integrations` (also runs from `seed_demo`) |
| Tests | `test_stage002.py`, `test_google_sheets_sync.py`, `test_crm_query.py`, `test_sync_throttle.py`, `test_source_sync_api.py` |

## API

API-INT-001 … API-INT-007 — see [api-contracts.md](../architecture/api-contracts.md).

## Production state (Google Sheets pilot)

| Component | Status |
|---|---|
| CRM leads | **Real** — Google Sheets → `CrmLead` cache |
| Clients to review | **Real** — derived from explicit `review_rules` on sync |
| Manager agent CRM | **Real** — NL → scoped SQL on cache; `as_of: last_sync_at` |
| Sync triggers | Hourly Beat + throttled login + on-demand (agent/manual) |
| Telephony metrics | Demo / degraded (not pilot path) |
| Reporting metrics | Demo sync |

Integrator setup: [integrator-vps-pilot.md](../operations/integrator-vps-pilot.md). Architecture: [integrations.md](../architecture/integrations.md).

## Demo state (local `seed_demo`)

- ОП Москва: CRM connected, telephony **degraded**, reporting connected
- ОП СПб: CRM connected, telephony **disconnected**
- Sample telephony recording + transcript for `employee@demo.local`

Demo seeds exercise UI with synthetic metrics; **pilot VPS uses real Sheets**, not demo CRM rows.

## Not in this slice

- User Level Integration settings UI (Admin only)
- Real telephony webhook / reporting API adapters
- CRM write-back to Sheets
- S3 media storage

## QA

```bash
python manage.py test integrations
```

Key modules: `test_stage002`, `test_google_sheets_sync`, `test_crm_query`, `test_sync_throttle`, `test_source_sync_api`.

## Related Docs

- [roadmap.md](../project/roadmap.md)
- [data-integration.md](../features/data-integration/data-integration.md)
- [integrations.md](../architecture/integrations.md)
- [integrator-vps-pilot.md](../operations/integrator-vps-pilot.md)
