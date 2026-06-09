Doc ID: LEGAL-PRIVACY-NOTES-001
Status: active
Source of truth: yes
Owner: product
Related docs: docs/security/data-retention.md, docs/architecture/integrations.md
Update trigger: новый тип данных, внешний процессор, изменение срока хранения
Review required: product, legal

# Privacy Policy Notes

## Purpose

Заметки для политики конфиденциальности SaaS-платформы AI Sales OS: записи разговоров, транскрипты, AI-обработка, права пользователей.

## Data Collected

| Data Type | Example | Required For Product | Source |
|---|---|---|---|
| Account | email, full name, role | yes | user / admin |
| Org structure | tenant, workspace, manager hierarchy | yes | admin |
| Conversation metadata | client name, employee, duration | yes | telephony / manual import |
| Transcripts | text + structured JSON segments | yes | ASR (demo until production STT) |
| AI chat | agent messages, client context | yes | user |
| Permissions | module levels, KB grants | yes | manager |

**Audio recordings are not stored** — only derived transcripts (see retention below).

## Processing Purposes

| Purpose | Data Used | User Visible |
|---|---|---|
| Sales quality analytics | transcripts, criteria | yes (manager dashboards) |
| AI assistant (RAG) | KB articles, transcripts, chat | yes |
| Access control | permissions, audit log | yes (settings) |

## Storage And Retention

| Data Type | Stored Where | Retention Period | Deletion Rule |
|---|---|---|---|
| Transcripts + recording metadata | PostgreSQL | **90 days** | Automated purge (see `data-retention.md`) |
| Audio | Not stored | 0 | N/A |
| Knowledge base | PostgreSQL | Until removed | Manual |
| Audit log (permissions) | PostgreSQL | 1 year (planned) | Archive |

## Third-Party Services

| Service | Data Shared | Purpose | Notes |
|---|---|---|---|
| OpenRouter (or compatible LLM API) | Prompt text, KB excerpts, analytics context | Chat, embeddings, report summaries | API keys per tenant/workspace in Django Admin (encrypted) |
| PostgreSQL | All application data | Primary database | Self-hosted / cloud |
| Redis | Celery task metadata | Background jobs | No PII in task args beyond IDs |

Production STT provider (Whisper/Deepgram/etc.) — **planned**; audio processed transiently only.

## User Rights

| Request Type | Supported (MVP) | Handling Rule |
|---|---|---|
| Export data | partial | Manual via admin |
| Delete account | partial | Admin deactivation |
| Withdraw consent | no | Planned with legal review |

## Open Questions

| Question | Owner | Status |
|---|---|---|
| Agent chat retention period | product | open |
| Analytics report retention | product | open |
| DPA template for enterprise tenants | legal | open |
