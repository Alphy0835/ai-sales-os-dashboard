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

| Source type | Code | Provides | Adapter |
|---|---|---|---|
| CRM | `crm` | deals, revenue | **amoCRM** (production) or demo metrics fallback |
| Telephony | `telephony` | calls, quality_score | demo sync (webhook deferred) |
| Reporting | `reporting` | meetings, revenue | demo sync |

### Production CRM — amoCRM (P4)

First production connector: **amoCRM** REST API (read-only metrics).

| Metric | amoCRM source | Maps to |
|---|---|---|
| `deals` | Won/closed deals count per responsible user for period | `MetricSnapshot.metric_key=deals` |
| `revenue` | Sum of deal budgets for period | `MetricSnapshot.metric_key=revenue` |

Credentials stored encrypted on `IntegrationSource.credentials_encrypted` (long-lived token + subdomain). Employee mapping: `User.email` or `User.external_id` ↔ amoCRM user. Configure via Django Admin (Integration Level MVP).

**Not in P4:** telephony webhook, reporting real adapters, CRM write-back.

## Sync pipeline

1. `IntegrationSource` row per tenant/workspace with `status`.
2. Celery task `integrations.sync_source` → `run_source_sync()` writes `MetricSnapshot` rows (amoCRM when credentials present, else demo).
3. Celery Beat `integrations.sync_all_sources` — daily 01:00 UTC.
4. Manual trigger: `POST /integrations/sources/{id}/sync/` (manager).
5. `GET /integrations/metrics/` aggregates snapshots + source health → `completeness` field.

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
| Audio files | **Not persisted** — validated on upload, discarded after processing |
| Transcripts | PostgreSQL `Transcription.text` + `content_json` (90-day retention) |

## Related Docs

- [api-contracts.md](api-contracts.md) — API-INT-*
- [secrets-management.md](../security/secrets-management.md)
