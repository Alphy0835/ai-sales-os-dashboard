Doc ID: ARCH-WORK-RULES-001
Status: active
Source of truth: yes
Owner: architecture
Related docs: docs/architecture/system-overview.md, docs/architecture/stack.md, docs/sync-checklist.md
Update trigger: новый architecture-документ или изменение структуры папки
Maturity: L2

# Architecture — Work Rules

Папка `architecture/` — карта системы, контракты, данные, интеграции, ADR.

| Файл | Назначение | Status |
|---|---|---|
| [stack.md](stack.md) | Подтверждённый technology stack | active |
| [system-overview.md](system-overview.md) | Модули, диаграмма, monorepo layout | active |
| [architecture-decisions/ADR-0001-*](architecture-decisions/ADR-0001-django-nextjs-monorepo.md) | Почему Django + Next.js | active |
| [api-contracts.md](api-contracts.md) | REST endpoints (source of truth) | STAGE-001 active |
| [data-model.md](data-model.md) | Сущности и правила данных | STAGE-001 active |
| [integrations.md](integrations.md) | Внешние сервисы | draft (STAGE-002) |

Правило: не дублировать API/данные в feature-файлах — ссылаться на api-contracts и data-model.