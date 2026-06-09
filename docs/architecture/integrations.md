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

Внешние источники данных для User Level (STAGE-002). Настройка credentials — Integration Level (Django Admin / post-MVP).

## Sources (MVP)

| Source type | Code | Provides | Demo adapter |
|---|---|---|---|
| CRM | `crm` | deals, revenue | `integrations.services.sync` |
| Telephony | `telephony` | calls, quality_score | sync + webhook stub |
| Reporting | `reporting` | meetings, revenue | sync |

## Sync pipeline

1. `IntegrationSource` row per tenant/workspace with `status`.
2. Celery task `integrations.sync_source` → `run_source_sync()` writes `MetricSnapshot` rows.
3. `GET /integrations/metrics/` aggregates snapshots + source health → `completeness` field.

Schedule: manual / seed for MVP; periodic Celery beat — post-MVP.

## Recordings & transcription

| Channel | Code | API |
|---|---|---|
| Telephony ingest | `telephony` | Integration Level webhook (planned) |
| Manual upload | `manual` | `POST /integrations/recordings/` |

Celery task `integrations.transcribe_recording` — MVP demo text in `Transcription.content_json`; **production STT deferred** (pluggable adapter, transient audio only).

Scheduled purge: `integrations.purge_expired_transcripts` — deletes recordings/transcripts older than `TRANSCRIPT_RETENTION_DAYS` (default 90).

## Storage

| Asset | Location |
|---|---|
| Audio files | **Not persisted** — validated on upload, discarded after processing |
| Transcripts | PostgreSQL `Transcription.text` + `content_json` (90-day retention) |

## Related Docs

- [api-contracts.md](api-contracts.md) — API-INT-*
- [secrets-management.md](../security/secrets-management.md)
