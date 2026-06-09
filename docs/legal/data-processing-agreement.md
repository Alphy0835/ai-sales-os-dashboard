Doc ID: LEGAL-DPA-001
Status: active
Source of truth: yes
Owner: legal
Related docs: docs/legal/privacy-policy-notes.md, docs/security/data-retention.md, docs/security/privacy-and-compliance.md, docs/security/incident-response.md
Update trigger: новый subprocessor, тип данных, срок хранения, или enterprise contract template
Review required: legal, product, security
Maturity: L2

# Data Processing Agreement

Шаблон требований DPA для B2B-клиентов AI Sales OS. Не юридический текст — таблицы для согласования с counsel перед enterprise-продажами.

## Purpose

DPA нужен, когда **клиент (Controller)** поручает **AI Sales OS (Processor)** обработку персональных данных сотрудников и контактов клиентов: транскрипты разговоров, метаданные звонков, учётные записи, AI-аналитика.

Применяется к: SaaS multi-tenant договорам с записями/транскриптами и AI-функциями. Self-hosted или demo-only — отдельное согласование.

## Parties And Roles

| Party | Role | Notes |
|---|---|---|
| Customer (tenant org) | **Controller** | Определяет правовое основание для записи разговоров сотрудников и клиентов; управляет пользователями и scope |
| AI Sales OS (product operator) | **Processor** | Обрабатывает данные по инструкциям клиента в рамках продукта |
| OpenRouter (or compatible LLM API) | **Subprocessor** | Inference/embeddings; prompts содержат выдержки KB и контекст аналитики |
| Hosting provider (Postgres/Redis/app) | **Subprocessor** | Infrastructure; регион по фактическому деплою |
| Future STT provider (Whisper/Deepgram/etc.) | **Subprocessor (planned)** | Transient audio only when ASR enabled — not in MVP |

## Data Categories

| Category | Examples | Sensitivity | Related Docs |
|---|---|---|---|
| Account & identity | email, full name, role, password hash | personal | [privacy-policy-notes.md](privacy-policy-notes.md) |
| Org structure | tenant, workspace, manager hierarchy, module permissions | internal / personal | [data-model.md](../architecture/data-model.md) |
| Conversation metadata | client name, employee, duration, funnel stage | confidential | [data-classification.md](../security/data-classification.md) |
| Transcripts | text, `content_json` segments | confidential | [data-retention.md](../security/data-retention.md) — **90 days** |
| Knowledge base | articles, embeddings, per-user grants | confidential | FEAT-010 / `KnowledgeArticleGrant` |
| AI chat | agent messages, client context, sources JSON | confidential | Indefinite (MVP — open policy) |
| Audit log | permission changes, scope denied, IP | internal | 1 year planned archival |
| Audio recordings | — | N/A | **Not stored** — transient processing only when ASR ships |

## Processing Purposes

| Purpose | Data Categories | Product Feature | Related Docs |
|---|---|---|---|
| User authentication & authorization | account, permissions, audit | FEAT-001 Access & Permissions | [auth-and-access-control.md](../security/auth-and-access-control.md) |
| Sales quality analytics | transcripts, criteria, metrics | FEAT-007 Quality AI Analytics | [quality-ai-analytics.md](../features/quality-ai-analytics/quality-ai-analytics.md) |
| Manager review workflow | clients to review, reviews, tasks | FEAT-003 Review Cycle | [review-cycle.md](../features/review-cycle/review-cycle.md) |
| AI assistant (RAG) | KB articles, grants, transcripts, chat | FEAT-010 / FEAT-011 | [knowledge-base-ai-agents.md](../features/knowledge-base-ai-agents/knowledge-base-ai-agents.md) |
| Data integration (demo) | metrics snapshots, recording metadata | FEAT-002 | [data-integration.md](../features/data-integration/data-integration.md) |
| Automated retention | transcripts, recording metadata | Ops / compliance | Celery `purge_expired_transcripts` |

## Subprocessors

| Service | Purpose | Data Shared | Region | Notes |
|---|---|---|---|---|
| PostgreSQL (self-hosted or managed) | Primary application database | All persisted application data | Deployer's choice | Backups per [backup-and-restore.md](../operations/backup-and-restore.md) |
| Redis | Celery broker | Task IDs, minimal metadata | Same as app | No full PII in task payloads by design |
| OpenRouter (compatible LLM API) | Chat, embeddings, report summaries | Prompt text, KB excerpts, analytics context | Provider-dependent | Keys per tenant/workspace in Django Admin (Fernet) |
| Future STT provider | Speech-to-text | Transient audio buffer | TBD | **Deferred** — MVP uses demo transcript text |

See also [integrations.md](../architecture/integrations.md).

## Security Measures

| Measure | Implemented | Related Docs |
|---|---|---|
| Access control (JWT, modules, scope, ceiling) | **yes** | [auth-and-access-control.md](../security/auth-and-access-control.md) |
| Multi-tenant isolation (`tenant_id` in views) | **yes** | [data-model.md](../architecture/data-model.md), [threat-model.md](../security/threat-model.md) |
| Secrets management | **yes** (env + Admin Fernet) | [secrets-management.md](../security/secrets-management.md) |
| Audit logging | **yes** (permission + scope denied) | [audit-logging.md](../security/audit-logging.md) |
| Rate limiting (login, agent) | **yes** | `THROTTLE_LOGIN`, `THROTTLE_AGENT` |
| Backup / restore | **yes** (scripts + docs) | [backup-and-restore.md](../operations/backup-and-restore.md) |
| Incident response | **yes** (runbook) | [incident-response.md](../security/incident-response.md) |
| httpOnly JWT / CSP | **no** (MVP gap) | [threat-model.md](../security/threat-model.md) T1 |

## Data Return / Deletion

| Scenario | Action | Timeframe | Related Docs |
|---|---|---|---|
| Contract ends | Export (manual Admin) + delete tenant data | Within **30 days** of termination (contract default — legal to confirm) | [data-retention.md](../security/data-retention.md) |
| Customer requests deletion (subject) | Admin deactivation; transcript purge on schedule | Transcripts: max **90 days** automated; account: manual MVP | [privacy-policy-notes.md](privacy-policy-notes.md) |
| Automated transcript expiry | Hard delete recordings + transcriptions | **90 days** (`TRANSCRIPT_RETENTION_DAYS`) | `integrations.purge_expired_transcripts`, `manage.py purge_transcripts` |
| Backup retention | Encrypted off-host copies | **≥30 days** prod recommendation | [backup-and-restore.md](../operations/backup-and-restore.md) — may contain deleted data until backup expiry |
| Knowledge base | Manual delete/deactivate | On customer instruction | Not covered by 90d purge |

## Incident Notification

| Incident Type | Notify Customer | Target Time | Related Docs |
|---|---|---|---|
| Personal data breach (confirmed) | **yes** | Without undue delay; **72h** GDPR-style target for processor→controller | [incident-response.md](../security/incident-response.md), [incident-notification.md](../operations/incident-notification.md) |
| Unauthorized access (single account) | **yes** if tenant data at risk | < **24h** | [incident-response.md](../security/incident-response.md) Scenario 2 |
| Service outage (no data impact) | optional | Per SLA | [service-levels.md](../operations/service-levels.md) |
| Scope/tenant bug (confirmed leak) | **yes** | Immediate | Scenario 1 in incident-response |

## Open Questions

| Question | Owner | Status |
|---|---|---|
| Final DPA legal text for RU/EU jurisdictions | legal | open |
| Agent chat + analytics report retention in DPA | product | open |
| STT subprocessor addendum when ASR ships | legal + backend | open |
| Standard SLA and breach notification contacts | operations | open |

## Related Docs

- [privacy-policy-notes.md](privacy-policy-notes.md)
- [privacy-and-compliance.md](../security/privacy-and-compliance.md)
- [data-classification.md](../security/data-classification.md)
- [data-retention.md](../security/data-retention.md)
- [audit-logging.md](../security/audit-logging.md)
- [access-review.md](../security/access-review.md)
- [incident-notification.md](../operations/incident-notification.md)
- [integrations.md](../architecture/integrations.md)
