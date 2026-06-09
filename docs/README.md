Doc ID: DOCS-INDEX-001
Status: active
Source of truth: yes
Owner: product
Related docs: docs/sync-checklist.md, docs/maturity-levels.md, docs/work-rules-docs.md
Update together with: sync-checklist.md, work-rules-docs.md
Update trigger: новый раздел docs, monorepo layout или architecture baseline
Review required: product
Maturity: L2

# Docs — Index

Пакет документации AI Sales OS. Код: monorepo в корне репозитория (`apps/api`, `apps/web`).

## Quick Links

| Задача | Документ |
|---|---|
| Идея продукта | [project-idea.md](../project-idea.md) |
| Требования | [product-requirements.md](project/product-requirements.md) |
| Roadmap | [project/roadmap.md](project/roadmap.md) |
| **Стек и архитектура** | [architecture/stack.md](architecture/stack.md) → [system-overview.md](architecture/system-overview.md) |
| API контракты | [architecture/api-contracts.md](architecture/api-contracts.md) |
| Модель данных | [architecture/data-model.md](architecture/data-model.md) |
| Backend | [backend/backend-docs.md](backend/backend-docs.md) |
| Frontend / routes | [frontend/frontend-docs.md](frontend/frontend-docs.md) |
| Design / preview | [project/design-guide/pages-map.md](project/design-guide/pages-map.md) |
| Локальный запуск | [operations/environments.md](operations/environments.md) |
| Синхронизация docs | [sync-checklist.md](sync-checklist.md) |

## Структура папки

| Папка | Назначение |
|---|---|
| `architecture/` | stack, system-overview, ADR, api-contracts, data-model, integrations |
| `backend/` | Django apps, handlers, Celery |
| `frontend/` | Next.js routes, components, API usage |
| `features/` | FEAT-001 … FEAT-007 по roadmap |
| `project/` | PRD, roadmap, user-flow, roles, design-guide |
| `security/` | auth, data classification, audit |
| `operations/` | environments, deployment, monitoring |
| `quality/` | acceptance criteria, DoD, release |
| `marketing/`, `product/`, `legal/`, `support/` | go-to-market и compliance (шаблоны) |

## Monorepo (код)

| Path | Stack |
|---|---|
| `apps/api/` | Django 5 + DRF + Celery |
| `apps/web/` | Next.js 15 + Tailwind |

См. [README.md](../README.md) в корне репозитория.

## Правила работы с файлами

- Doc ID стабилен; история — в git.
- Source of truth для API — `api-contracts.md`; для данных — `data-model.md`.
- Перед завершением правок — [sync-checklist.md](sync-checklist.md).
