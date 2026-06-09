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
| Audio files | **Not persisted** | N/A | Discarded after STT processing |
| Knowledge base articles | PostgreSQL | Until deactivated/deleted | Manual or tenant offboarding |
| Agent chat messages | PostgreSQL | **90 days** | Hard delete via Celery `ai.purge_expired_agent_chats` |
| Analytics reports | PostgreSQL | Indefinite (MVP) | Future policy |

## Transcript retention (90 days)

- Setting: `TRANSCRIPT_RETENTION_DAYS=90` (default)
- Celery task: `integrations.purge_expired_transcripts`
- Ops command: `python manage.py purge_transcripts --dry-run`

Records older than the retention window are **hard deleted** (`ConversationRecording` + related `Transcription`).

## Agent chat retention (90 days)

- Setting: `AGENT_CHAT_RETENTION_DAYS=90` (default)
- Celery task: `ai.purge_expired_agent_chats` (daily 04:00 UTC via Beat)
- Ops command: `python manage.py purge_agent_chats --dry-run`

Sessions older than the retention window are **hard deleted** (`AgentChatSession` + related `AgentChatMessage` via CASCADE).

## Audio policy

Call audio is **not stored** in the database or object storage. Upload/webhook flows validate input and generate transcripts only. When ASR is enabled, audio will be processed in a temporary buffer and discarded after transcription.

## Related docs

- `docs/legal/privacy-policy-notes.md`
- `docs/architecture/integrations.md`
