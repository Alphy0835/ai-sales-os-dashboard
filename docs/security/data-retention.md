Doc ID: SECURITY-DATA-RETENTION-001
Status: active
Source of truth: yes
Owner: backend
Related docs: docs/legal/privacy-policy-notes.md, docs/architecture/integrations.md
Update trigger: изменение сроков хранения или политики удаления
Review required: backend, legal

# Data Retention

## Summary

| Data type | Stored where | Retention | Deletion |
|---|---|---|---|
| Conversation transcripts (`Transcription.text`, `content_json`) | PostgreSQL | **90 days** | Hard delete via Celery job |
| Recording metadata (`ConversationRecording` without audio) | PostgreSQL | **90 days** | Cascade with transcript purge |
| Audio files | **Not persisted** | N/A | Discarded after processing (ASR deferred) |
| Knowledge base articles | PostgreSQL | Until deactivated/deleted | Manual or tenant offboarding |
| Agent chat messages | PostgreSQL | Indefinite (MVP) | Future policy |
| Analytics reports | PostgreSQL | Indefinite (MVP) | Future policy |

## Transcript retention (90 days)

- Setting: `TRANSCRIPT_RETENTION_DAYS=90` (default)
- Celery task: `integrations.purge_expired_transcripts`
- Ops command: `python manage.py purge_transcripts --dry-run`

Records older than the retention window are **hard deleted** (`ConversationRecording` + related `Transcription`).

## Audio policy

Call audio is **not stored** in the database or object storage. Upload/webhook flows validate input and generate transcripts only. When ASR is enabled, audio will be processed in a temporary buffer and discarded after transcription.

## Related docs

- `docs/legal/privacy-policy-notes.md`
- `docs/architecture/integrations.md`
