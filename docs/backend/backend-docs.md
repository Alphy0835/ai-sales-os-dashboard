Doc ID: BACKEND-DOCS-001
Status: active
Source of truth: yes
Owner: backend
Related docs: docs/architecture/system-overview.md, docs/architecture/api-contracts.md, docs/architecture/data-model.md, docs/project/roadmap.md, docs/features/*
Update together with: api-contracts.md, data-model.md, system-overview.md
Update trigger: новый Django app, модуль, handler или изменение границ backend
Review required: backend, security
Maturity: L2

# Backend Docs

## Purpose

Django monolith (`apps/api`) — REST API для User Level UI, фоновые задачи (Celery), Django Admin для Integration Level. Не отдаёт HTML для пользовательских экранов.

> Stack: [system-overview.md](../architecture/system-overview.md) · Контракты: [api-contracts.md](../architecture/api-contracts.md)

## Backend Scope

| Area | Included | Notes | Related Docs |
|---|---|---|---|
| API | yes | REST `/api/v1/*`, DRF | api-contracts.md |
| Auth | yes | JWT + custom User model | security/auth-and-access-control.md |
| Data access | yes | Django ORM, migrations | data-model.md |
| Integrations | planned | Adapters + Celery | integrations.md |
| Background jobs | yes | Celery + Redis | STAGE-002+ |
| Admin actions | yes | Django Admin | Integration Level |

## Repository Layout

```
apps/api/
├── config/           # settings, urls, celery, wsgi
├── core/             # health, middleware, base models
├── accounts/         # STAGE-001: tenant, user, permissions
├── integrations/     # STAGE-002: sources, metrics, recordings
├── manage.py
└── requirements.txt
```

Planned apps (by roadmap): `integrations`, `analytics`, `reviews`, `ai`.

## Modules / Services

| Django app | Responsibility | Main entities | Roadmap | Feature |
|---|---|---|---|---|
| `core` | Tenant middleware, health, timestamps | — | STAGE-001 | — |
| `accounts` | Auth, RBAC, scope, ceiling rule, audit | Tenant, Workspace, User, ModulePermission, ManagerScope, AuditLog | STAGE-001 | FEAT-001 |
| `integrations` | CRM/telephony sync, recordings, transcription | IntegrationSource, MetricSnapshot, ConversationRecording, Transcription | STAGE-002 | FEAT-002 |
| `analytics` | KPI aggregates, dashboard API | MetricSnapshot, ClientToReview | STAGE-003 | FEAT-003 |
| `reviews` | Reviews, tasks | Review, Task | STAGE-004 | FEAT-004 |
| `ai` | RAG, agents, custom reports | KnowledgeChunk, ChatSession | STAGE-005–006 | FEAT-005–007 |

## API Handlers (map)

| Route group | App | Auth | Contract doc |
|---|---|---|---|
| `/api/v1/auth/*` | accounts | public / JWT | API-AUTH-* |
| `/api/v1/scope/*` | accounts | JWT | API-SCOPE-* |
| `/api/v1/permissions/*` | accounts | JWT + settings | API-PERM-* |
| `/api/v1/audit/permissions/` | accounts | JWT + settings | API-AUDIT-001 |
| `/api/v1/integrations/*` | integrations | JWT + dashboard | API-INT-* |
| `/api/v1/manager/*` | analytics | JWT + manager | API-MGR-* |
| `/api/v1/employee/dashboard/` | analytics | JWT + employee | API-EMP-001 |
| `/api/v1/health/` | core | public | API-HEALTH-001 |
| `/api/v1/manager/*` | analytics, reviews, … | JWT + manager role | TBD per stage |
| `/api/v1/employee/*` | analytics, reviews, … | JWT + employee role | TBD per stage |
| `/admin/` | Django Admin | session | Integration Level |

OpenAPI: `/api/schema/` (drf-spectacular).

## Data Access

| Data area | Storage | Pattern |
|---|---|---|
| Tenants, users, permissions | PostgreSQL | ORM; all queries filtered by `tenant_id` |
| KPI, reviews | PostgreSQL | ORM + Celery aggregation |
| Recordings | S3 + PostgreSQL metadata | Upload → task |
| Embeddings | PostgreSQL pgvector | STAGE-006 |

## Background Jobs (Celery)

| Task | Trigger | Stage |
|---|---|---|
| `sync_integration_source` | manual / seed | STAGE-002 |
| `transcribe_recording` | upload / telephony ingest | STAGE-002 |
| `embed_knowledge_chunk` | KB update | STAGE-006 |

## Local Development

```bash
docker compose up -d postgres redis
cd apps/api && pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8000
celery -A config worker -l info
```

See [environments.md](../operations/environments.md).

## Related Docs

- [frontend-docs.md](../frontend/frontend-docs.md) — API consumer
- [pages-map.md](../project/design-guide/pages-map.md) — screens driving endpoints
