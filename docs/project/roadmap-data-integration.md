Doc ID: ROADMAP-STAGE-002
Status: active
Source of truth: yes
Owner: backend
Related docs: docs/project/roadmap.md, docs/features/data-integration/data-integration.md
Update trigger: новый adapter, endpoint или sync job
Review required: backend, QA

# STAGE-002 — Data Integration (Implementation)

**Completed:** 2026-06-09 (backend MVP)

## Summary

Integration sources with health status, metric aggregation API with partial/empty states, manual recording upload + Celery transcription pipeline.

## Code

| Area | Path |
|---|---|
| Django app | `apps/api/integrations/` |
| Models | IntegrationSource, MetricSnapshot, ConversationRecording, Transcription |
| Sync | `integrations/services/sync.py`, task `integrations.sync_source` |
| Aggregation | `integrations/services/aggregation.py` |
| Transcription | `integrations/tasks.py` → `transcribe_recording` |
| Seed | `python manage.py seed_integrations` (also runs from `seed_demo`) |
| Tests | `integrations/tests/test_stage002.py` |

## API

API-INT-001 … API-INT-007 — see [api-contracts.md](../architecture/api-contracts.md).

## Demo state

- ОП Москва: CRM connected, telephony **degraded**, reporting connected
- ОП СПб: CRM connected, telephony **disconnected**
- Sample telephony recording + transcript for `employee@demo.local`

## Not in this slice

- Real CRM/telephony API adapters (Integration Level)
- Production STT provider
- Dashboard UI consumption (STAGE-003)
- S3 media storage

## QA

`python manage.py test integrations.tests.test_stage002`

## Related Docs

- [roadmap.md](../project/roadmap.md)
- [data-integration.md](../features/data-integration/data-integration.md)
