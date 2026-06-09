Doc ID: ADR-0001
Status: active
Source of truth: yes
Owner: architecture
Related docs: docs/architecture/system-overview.md, docs/backend/backend-docs.md, docs/frontend/frontend-docs.md
Update together with: system-overview.md
Update trigger: смена основного backend/frontend стека или monorepo layout
Review required: backend, frontend
Maturity: L2

# ADR-0001: Django + Next.js Monorepo (Variant A)

## Context

AI Sales OS — SaaS multi-tenant B2B продукт (solo fullstack). Нужны: RBAC + scope (STAGE-001), интеграции и фоновые jobs (STAGE-002), дашборды, RAG/AI (STAGE-006), админка для Integration Level. Кода в репозитории не было — выбор стека с нуля.

Рассматривали: Django monolith, FastAPI monolith, Django + FastAPI hybrid.

## Options

| Вариант | Суть |
|---|---|
| **A — Django + DRF + Next.js** | Django — domain, admin, API; Next.js — UI из design preview |
| **B — FastAPI + Next.js** | Async API, но RBAC/admin/multi-tenant с нуля |
| **C — Django + FastAPI AI service** | Два деплоя; оправдано позже при нагрузке на streaming/RAG |

## Decision

**Variant A:** PostgreSQL 16 + pgvector, Django 5 + DRF, Redis + Celery, Next.js (App Router) + TypeScript + Tailwind, S3-compatible storage, OpenAI через adapter.

- Multi-tenant MVP: **`tenant_id` на всех tenant-scoped таблицах** (не schema-per-tenant на старте).
- Auth User Level: **JWT access/refresh**; Django Admin — session для Integration Level.
- FastAPI: **не стартовый**; пересмотр после STAGE-006 при необходимости отдельного `ai-service`.

## Why

- Solo: один backend-процесс, Django Admin для интеграторов без отдельной админ-панели.
- Roadmap STAGE-001: встроенные patterns auth/permissions быстрее, чем сборка на FastAPI.
- UI уже утверждён в HTML preview — Next.js + design tokens, Django не отдаёт templates.
- Celery + Redis закрывают CRM sync, транскрипцию, embeddings без второго фреймворка.

## Consequences

**Плюсы:** быстрый vertical slice, предсказуемая структура apps, зрелая ORM/migrations, OpenAPI через drf-spectacular.

**Минусы:** streaming AI-chat — SSE/chunked в Django или вынос позже; нужно дисциплинированно держать tenant scope в queryset/middleware.

**Ограничения:** не смешивать User Level UI с Django templates; контракты API — source of truth в `api-contracts.md`.

## Related ADR

- *(будущее)* ADR-0002: tenant_id vs django-tenants
- *(будущее)* ADR-0003: FastAPI ai-service (если потребуется)
